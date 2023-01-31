import abc
import os
import pickle
from abc import ABC

import numpy as np
import pandas as pd

from peach.report.const import SEPARATOR


class ExportDataABC(ABC):
    def __init__(self, file_name, mode="ab+"):
        assert "a" in mode or "w" in mode
        if "b" not in mode:
            mode += "b"
        self._file_name = file_name
        self._pickle_file_name = file_name + ".pkl"
        self._mode = mode
        self._header = None
        self._del_col_index_list = None
        self._page_data = None
        self._first = True

    def process_page(self, page_data, **kwargs):
        self.pre_process(page_data, **kwargs)
        self.do_process_page()
        self.post_process()

    def pre_process(self, page_data, **kwargs):
        """
        预处理
        :param page_data: 分页数据 [[],[]......[]]
        :param kwargs:
            - header: 表头 {field: text, ......} / [text, ......]
            - include_fields: 需要导出的字段 "field1, field2, field3......"
        :return:
        """
        if not self._first:
            self._page_data = self._del_col_data(page_data)
            return

        header = kwargs.get("header")
        include_fields = kwargs.get("include_fields")
        if include_fields is not None:
            assert isinstance(
                header, dict
            ), "header must be dict when include_fields is not None"
            if include_fields:
                _include_fields_list = include_fields.split(SEPARATOR)
                self._header = [
                    v for k, v in header.items() if k in _include_fields_list
                ]
                self._del_col_index_list = self._del_col_index(
                    header, _include_fields_list
                )
                self._page_data = self._del_col_data(page_data)
            else:
                # include_fields 为空时, 过滤掉所有字段
                self._header = []
                self._del_col_index_list = list(range(len(header)))
                self._page_data = []
        else:
            # include_fields 为 None 时, 导出所有字段
            assert isinstance(
                header, (list, dict)
            ), "header must be list or dict when include_fields is None"
            self._header = header if isinstance(header, list) else list(header.values())
            self._del_col_index_list = []
            self._page_data = page_data

        self._first = False

    def do_process_page(self):
        self.to_pickle(self._page_data)

    def post_process(self):
        pass

    @abc.abstractmethod
    def export(self):
        pass

    @property
    def export_data(self) -> pd.DataFrame:
        try:
            return pd.DataFrame(self.read_pickle(), columns=self._header)
        finally:
            self.remove_pickle()

    def to_pickle(self, obj):
        with open(self._pickle_file_name, self._mode) as f:
            pickle.dump(obj, f)

    def read_pickle(self):
        with open(self._pickle_file_name, "rb") as f:
            while True:
                try:
                    for line in pickle.load(f):
                        yield line
                except EOFError:
                    break
        self.remove_pickle()

    def remove_pickle(self):
        if os.path.exists(self._pickle_file_name):
            os.remove(self._pickle_file_name)

    @staticmethod
    def _del_col_index(header, include_fields):
        _del_col_index = []
        for i, (k, _) in enumerate(header.items()):
            if k in include_fields:
                continue
            _del_col_index.append(i)

        return _del_col_index

    def _del_col_data(self, page_data):
        if not page_data or not self._header:
            return []

        if not self._del_col_index_list:
            return page_data

        return np.delete(page_data, self._del_col_index_list, axis=1)
