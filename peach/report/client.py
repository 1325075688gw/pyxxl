#! -*- coding:utf-8 -*-
import hashlib
import json
import logging
import os
import pickle
import typing
import uuid
import dataclasses
from collections import namedtuple
from datetime import datetime
from enum import unique, Enum
from functools import wraps
from typing import Type, Any

import requests
from dacite import from_dict, Config
from requests import RequestException

from . import filelock
from .dtos import TaskListCriteria
from .engines import Csv, Xlsx

from peach.django.json import JsonEncoder
from peach.misc import dt, retry

_LOGGER = logging.getLogger(__name__)

MAX_PAGE_NUMS = 100
MAX_RETRY_COUNT = 3


@unique
class _FileType(Enum):
    CSV = "csv"
    XLSX = "xlsx"


_ENGINES = {_FileType.CSV: Csv, _FileType.XLSX: Xlsx}

_FILE_EXTENSION = {
    _FileType.CSV: ".csv",
    _FileType.XLSX: ".xlsx",
}

ReportTaskInfo = namedtuple(
    "ReportTaskInfo",
    [
        "id",
        "report_type",
        "file_type",
        "file_name",
        "page_no",
        "page_size",
        "filter_params",
    ],
)


class ReportClient:
    """
    导出统一客户端。
    """

    FileType = _FileType
    report_types: typing.Dict[str, typing.Callable] = dict()

    def __init__(
        self, server_host, app_key, app_secret, temp_file_dir=None, debug=False
    ):

        self.debug = debug
        self.cur_task = dict()  # key task_id, value ReportTaskInfo

        if self.debug:
            _LOGGER.warning("Report is running under DEBUG mode")
            return

        assert server_host and isinstance(server_host, str)
        self.server_host = server_host
        self.app_key = app_key
        self.app_secret = app_secret

        temp_file_dir = temp_file_dir or "/tmp/export/"

        self.export_file_dir = os.path.join(temp_file_dir, "file/")
        if not os.path.exists(self.export_file_dir):
            os.makedirs(self.export_file_dir)

        assert os.access(
            temp_file_dir, os.W_OK
        ), "temp_file_dir directory not exists or not writable: {}".format(
            temp_file_dir
        )

        self.meta_file = os.path.join(temp_file_dir, "meta")

        self.engines = _ENGINES

    def add_report_task(
        self,
        report_type,
        file_type,
        user_id,
        page_size=1000,
        remark=None,
        filter_params=None,
    ):
        assert report_type in ReportClient.report_types
        assert isinstance(file_type, self.FileType)
        filter_params = filter_params or dict()
        file_name = self._gen_filename(file_type)
        params = dict(
            client_id=str(uuid.uuid4()),
            user_id=user_id,
            filter_params=filter_params,
            file_name=file_name,
            file_type=file_type.value,
            report_type=report_type,
            page_size=page_size,
            remark=remark,
        )
        return self._rpc_upload_task(**params)

    def list_tasks(self, criteria: TaskListCriteria):
        return self._rpc_list_task(criteria)

    def get_download_url(self, task_id):
        url = "get_download_url/"
        return self._do_get(self.server_host + url, dict(task_id=task_id))

    def load_cur_task(self):
        if self.debug:
            return
        self._load_conf_from_local()
        self.fetch_task()

    def fetch_task(self):
        self._rpc_fetch_task()

    def executor(self):
        self._executor()

    def _executor(self):
        _LOGGER.info(f"start export tasks: {len(self.cur_task)} now: {dt.local_now()}")
        for task_id in list(self.cur_task.keys()):
            try_count = 0
            success = False
            while try_count < MAX_RETRY_COUNT and not success:
                try:
                    report_task_info = self.cur_task[task_id]
                    func = ReportClient.report_types[report_task_info.report_type]
                    task_id = report_task_info.id

                    file_name = os.path.join(
                        self.export_file_dir, report_task_info.file_name
                    )
                    if os.path.exists(file_name):
                        os.remove(file_name)

                    engine = self.engines[self.FileType(report_task_info.file_type)](
                        file_name, mode="a+"
                    )

                    if report_task_info.filter_params:
                        filter_params = json.loads(report_task_info.filter_params)
                    else:
                        filter_params = dict()
                    filter_params["page_no"] = report_task_info.page_no
                    filter_params["page_size"] = report_task_info.page_size
                    items_count = 0
                    while True:
                        count, header, items = func(filter_params)
                        engine.process_page(items, header=header)

                        if not items:
                            break
                        items_count += count
                        filter_params["page_no"] += 1
                        if filter_params["page_no"] > MAX_PAGE_NUMS:
                            break
                    engine.export()
                    self._upload_file(task_id, items_count)
                    success = True
                except Exception as e:
                    try_count += 1
                    _LOGGER.exception(
                        f"cached executor export task: {e}, {task_id} - {try_count}",
                        exc_info=True,
                    )
            if not success:
                # self._rpc_update_task(task_id)
                pass
            del self.cur_task[task_id]
            _LOGGER.info(
                f"export task_id: {task_id} finished, tasks: {len(self.cur_task)}, now: {dt.local_now()}"
            )
            self._save_conf_to_local()

    def _update_cur_task(self, tasks):
        self.cur_task.update(tasks)
        self._save_conf_to_local()

    def _save_conf_to_local(self):
        """
        保存任务数据到本机磁盘
        """
        with filelock.FileLock(self.meta_file):
            with open(self.meta_file, "wb") as meta_f:
                meta_f.write(pickle.dumps(self.cur_task))

    def _load_conf_from_local(self):
        """
        从本机磁盘加载配置
        """
        try:
            with filelock.FileLock(self.meta_file):
                with open(self.meta_file, "rb") as meta_f:
                    self.cur_task = pickle.loads(meta_f.read())
        except FileNotFoundError:
            return False
        return True

    def _upload_file(self, task_id, items_count=None):
        url = "upload_file/"
        file_path = os.path.join(self.export_file_dir, self.cur_task[task_id].file_name)
        _LOGGER.info(f"upload file: {file_path}")
        with open(file_path, "rb") as f:
            files = {"export_file": f}

            self._do_post(
                self.server_host + url,
                dict(task_id=task_id, items_count=items_count),
                files=files,
            )

    def _rpc_list_task(self, criteria: TaskListCriteria):
        url = "task/"
        return self._do_get(self.server_host + url, dataclasses.asdict(criteria))

    def _rpc_fetch_task(self):
        url = "fetch_task/"
        nums = 1
        try:
            tasks = self._do_get(self.server_host + url, dict(nums=nums))
        except Exception:
            _LOGGER.exception("_rpc_fetch_task fail", exc_info=True)
            return
        if not tasks:
            return
        res = dict()
        for t in tasks:
            res[t["id"]] = ReportTaskInfo(
                t["id"],
                t["report_type"],
                t["file_type"],
                t["file_name"],
                t["page_no"],
                t["page_size"],
                t["filter_conditions"],
            )

        self._update_cur_task(res)

    def _rpc_update_task(self, task_id):
        url = "task/"
        return self._do_put(self.server_host + url, dict(task_id=task_id))

    def _gen_filename(self, file_type):
        return str(uuid.uuid4()) + _FILE_EXTENSION[file_type]

    @retry.retry(RequestException)
    def _rpc_upload_task(
        self,
        client_id,
        user_id,
        file_name,
        file_type,
        report_type,
        page_size,
        remark,
        filter_params,
    ):
        url = "task/"
        params = dict(
            client_id=client_id,
            user_id=user_id,
            filter_conditions=json.dumps(filter_params, cls=JsonEncoder),
            file_name=file_name,
            file_type=file_type,
            report_type=report_type,
            page_size=page_size,
            remark=remark,
        )
        return self._do_post(self.server_host + url, params)

    def _do_get(self, url, params):
        self._add_sign(params)
        _LOGGER.info("before get url: {}, params: {}".format(url, params))
        resp = requests.get(url, params, timeout=5)
        return self._decode_response(url, params, resp)

    def _do_post(self, url, params, files=None):
        self._add_sign(params)
        _LOGGER.info("before post url: {}, params: {}".format(url, params))
        resp = requests.post(url, data=params, files=files, timeout=5)
        return self._decode_response(url, params, resp)

    def _do_put(self, url, params):
        self._add_sign(params)
        _LOGGER.info("before put url: {}, params: {}".format(url, params))
        resp = requests.put(url, data=params, timeout=5)
        return self._decode_response(url, params, resp)

    def _decode_response(self, url, params, resp):
        _LOGGER.info(
            "request url: {}, params: {}, get resp: {} - {}".format(
                url, params, resp.status_code, resp.text
            )
        )
        try:
            resp_json = resp.json()
        except ValueError:
            raise ValueError("open api response is not valid")
        return resp_json["data"]

    def _add_sign(self, params):
        params["timestamp"] = int(dt.now_ts())
        params["app_key"] = self.app_key
        s = ""
        for k in sorted(params.keys()):
            if params[k] is not None:
                s += "{}={}&".format(k, params[k])
        s += "key=%s" % self.app_secret
        m = hashlib.md5()
        m.update(s.encode("utf8"))
        sign = m.hexdigest().upper()
        params["sign"] = sign

    @staticmethod
    def decorator(data_class):
        assert dataclasses.is_dataclass(data_class)

        def report_decorator(func):
            @wraps(func)
            def wrapper(filter_params):
                return func(_dict_to_dto(filter_params, data_class=data_class))

            return wrapper

        return report_decorator

    @staticmethod
    def register(report_type, func):
        if report_type in ReportClient.report_types:
            raise Exception(
                f"It is not allowed to register duplicated report_type: {report_type}"
            )
        ReportClient.report_types[report_type] = func


##################################################################################
def _dict_to_dto(data: dict, data_class: Type) -> Any:
    return from_dict(
        data_class=data_class,
        data=data,
        config=Config(
            cast=[Enum],
            type_hooks={
                datetime: lambda t: dt.parse_datetime(t),
                int: int,
            },
        ),
    )
