from dataclasses import is_dataclass, fields
import hashlib
import inspect
import json
import logging
import os
import pickle
import sys
import threading
import time
import typing
from datetime import datetime
from enum import Enum

import requests
import tomli
from dacite import from_dict, Config

from peach.misc import dt
from .six import urlparse

_LOGGER = logging.getLogger(__name__)


class GConfClient:
    """
    配置组件操作统一客户端。
    """

    def __init__(
        self,
        server_host,
        app_key,
        app_secret,
        conf_data_dir,
        cluster="default",
        full_pull_interval=300,
        debug=False,
    ):
        """
        :param server_host: 配置中心服务端地址
        :param app_key: 找配置中心管理员申请
        :param app_secret: 找配置中心管理员申请，注意不要泄漏
        :param conf_data_dir: 本地配置数据存储目录
        :param full_pull_interval: 周期全量同步数据间隔, 单位为秒
        :param cluster: 集群名称，默认为 default
        """
        self.debug = debug
        self.running: bool = False
        self.conf_items = dict()
        self.callbacks = dict()
        self.dataclasses = dict()

        # debug 模式下不启动远程配置加载
        if debug:
            return

        assert server_host and isinstance(server_host, str)
        assert cluster and isinstance(cluster, str)
        self.fetch_conf_url = urlparse.urljoin(server_host, "get_conf/")
        self.app_key = app_key
        self.app_secret = app_secret
        self.cluster = cluster
        self.full_pull_interval = full_pull_interval

        # 创建集群数据目录
        self.cluster_data_dir = os.path.join(conf_data_dir, cluster)
        if not os.path.exists(self.cluster_data_dir):
            os.makedirs(self.cluster_data_dir)
        # 当前配置元数据：当前使用版本
        self.conf_meta_file = os.path.join(self.cluster_data_dir, "meta")

        self.current_release = None

    def start(self):
        """
        启动客户端运行，主要执行任务：监控配置中心配置更改，和全量定期拉取同步最新全量配置。
        """
        self.running = True
        if self.debug:
            _LOGGER.warn("Gconf is running under DEBUG mode")
            return
        # 启动循环任务前，必须首次加载当前应用全部配置
        try:
            _LOGGER.info("load conf from remote server when first start service")
            self._load_conf_from_server()
        except Exception:
            _LOGGER.info(
                "load conf from remote server fail, try load from local cache data, cause: ",
                exc_info=True,
            )
            try:
                self._load_conf_from_local()
            except Exception:
                _LOGGER.exception("load conf from local fail")
                sys.exit(1)

        threading.Thread(target=self._monitor_updates, daemon=True).start()

    def bind_dataclass(self, name: str, data):
        assert is_dataclass(data)
        assert not inspect.isclass(data)
        if self.running:
            raise Exception(
                f"gconf is already started, bind_dataclass is not allowed: {name}"
            )
        if name in self.dataclasses:
            raise Exception(f"It is not allowed to bind duplicated dataclass: {name}")
        _LOGGER.info(
            f"gconf bind dataclass, name: {name}, dataclass: {data.__class__.__name__}"
        )
        self.dataclasses[name] = data

    def register_callback(self, name, callback):
        """
        注册配置更新回调处理器
        :return:
        """
        if self.running:
            raise Exception(
                f"gconf is already started, register_callbacks is not allowed: {name}"
            )
        _LOGGER.info(
            f"gconf register callbacks, name: {name}, dataclass: {callback.__name__}"
        )
        self.callbacks[name] = callback

    def decorator(self):
        """
        用来配置类装饰器
        :return:
        """

        def conf_decorator(name, target: typing.Type = None):
            def wrapper(cls):
                def __getattribute__(_self, item):
                    if target is None:
                        try:
                            return self.get_dict(name)[item]
                        except KeyError:
                            return super(cls, _self).__getattribute__(item)
                    else:
                        if self.conf_items:
                            return from_dict(
                                data_class=target, data=self.get_dict(name)
                            )
                        else:
                            return super(cls, _self).__getattribute__(item)

                cls.__getattribute__ = __getattribute__
                return cls()

            return wrapper

        return conf_decorator

    def get_int(self, name, default=None) -> int:
        if default is not None:
            assert isinstance(default, int)
        return int(self.get_value(name, default))

    def get_float(self, name, default=None) -> float:
        if default is not None:
            assert isinstance(default, float)
        return float(self.get_value(name, default))

    def get_bool(self, name, default=None) -> bool:
        if default is not None:
            assert isinstance(default, bool)
        return self.get_value(name, default) in ["true", "1", "True"]

    def get_dict(self, name, default=None) -> typing.Dict:
        if default is not None:
            assert isinstance(default, (dict, list))

        value = self.get_value(name, default)
        if isinstance(value, (dict, list)):
            return value
        else:
            raw = self.get_value(name, default)
            try:
                if name.endswith("json"):
                    value = json.loads(raw)
                elif name.endswith("toml"):
                    value = tomli.loads(raw)  # type: ignore
                self.conf_items[name] = value
            except Exception:
                _LOGGER.exception(
                    f"gconf get_dict fail, the value has invalid format: {name}"
                )
                raise
            return value  # type: ignore

    def get_value(self, name, default=None) -> str:
        value = self.conf_items.get(name)
        if value is None and default is not None:
            value = default
        if value is None:
            raise KeyError(
                "conf name is not config, you can config in server or give a default value, name: [{}]".format(
                    name
                )
            )
        return value

    def _load_conf_from_server(self):
        """
        从配置中心服务器拉取最新配置
        """
        return self._fetch_conf()

    def _load_conf_from_local(self):
        """
        从本机磁盘加载配置
        """
        try:
            with open(self.conf_meta_file, "r") as meta_f:
                self.current_release = meta_f.read()
                with open(
                    os.path.join(self.cluster_data_dir, self.current_release), "rb"
                ) as release_f:
                    self.conf_items = pickle.loads(release_f.read())
        except FileNotFoundError:
            return False
        self._exec_callbacks(True)
        return True

    def _save_conf_to_local(self):
        """
        保存配置数据到本机磁盘
        """
        assert self.current_release and self.conf_items

        with open(
            os.path.join(self.cluster_data_dir, self.current_release), "wb"
        ) as release_f:
            release_f.write(pickle.dumps(self.conf_items))
        with open(self.conf_meta_file, "w") as meta_f:
            meta_f.write(self.current_release)

    def _monitor_updates(self):
        """
        监控配置实时更新
        """
        _LOGGER.info("the daemon task run in background to monitor the conf updated")
        while True:
            try:
                self._fetch_conf(first=False)
            except Exception:
                _LOGGER.exception("fetch updated release fail in monitor stage")
                time.sleep(10)

    def _fetch_conf(self, first=True):
        params = {
            "app_key": self.app_key,
            "cluster": self.cluster,
            "exist_release": self.current_release,
        }
        self._add_sign(params)

        try:
            _LOGGER.info("begin fetch the latest release, params: {}".format(params))
            resp = requests.get(
                self.fetch_conf_url,
                params=params,
                timeout=5 if first else self.full_pull_interval,
            )
            if resp.status_code != 200:
                raise Exception(
                    "load conf from remote fail, the response is : {} - {}".format(
                        resp.status_code, resp.text
                    )
                )
        except requests.RequestException as ex:
            if first:
                raise
            else:
                if isinstance(ex, requests.exceptions.ReadTimeout):
                    _LOGGER.info("no updated release")
                    return
                else:
                    raise

        data = resp.json()
        _LOGGER.info("success get updated release: {}".format(self.current_release))

        # 创建一个新的配置容器，不基于原先操作，保持数据一致性，不然可能混杂不同配置版本数据
        new_conf_items = dict()
        for item in data["confs"]:
            new_conf_items[item["name"]] = item["value"]
        self.conf_items = new_conf_items
        self.current_release = data["release"]
        assert self.current_release and self.conf_items

        self._exec_callbacks(first)

        # 保存在本机
        self._save_conf_to_local()

    def _exec_callbacks(self, first):
        # process dataclass bind
        for name, data in self.dataclasses.items():
            if name in self.conf_items:
                data_new = from_dict(
                    data_class=type(data),
                    data=self.get_dict(name),
                    config=Config(
                        cast=[Enum],
                        type_hooks={
                            datetime: lambda t: dt.from_timestamp(int(int(t) / 1000)),
                            int: int,
                        },
                    ),
                )
                for field in fields(type(data)):
                    setattr(data, field.name, getattr(data_new, field.name))

        # 处理回调函数
        for name, callback in self.callbacks.items():
            if name in self.conf_items:
                try:
                    _LOGGER.info(
                        "begin exec conf callback, {} - {}".format(name, callback)
                    )
                    callback(self.conf_items[name])
                except Exception:
                    _LOGGER.exception(
                        "exec conf callback fail, {} - {}".format(name, callback)
                    )
                    if first:
                        sys.exit(1)

    def _add_sign(self, params):
        params["timestamp"] = int(datetime.now().timestamp())
        s = ""
        for k in sorted(params.keys()):
            if params[k]:
                s += "{}={}&".format(k, params[k])
        s += "key=%s" % self.app_secret
        m = hashlib.md5()
        m.update(s.encode("utf8"))
        sign = m.hexdigest().upper()
        params["sign"] = sign
