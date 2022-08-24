import abc
import os
import pickle
from abc import ABC
import pandas as pd


class ExportDataABC(ABC):
    def __init__(self, file_name, mode="ab+"):
        assert "a" in mode or "w" in mode
        if "b" not in mode:
            mode += "b"
        self._file_name = file_name
        self._pickle_file_name = file_name + ".pkl"
        self._mode = mode
        self._header = None

    def process_page(self, page_data, **kwargs):
        self.pre_process(page_data, **kwargs)
        self.do_process_page(page_data, **kwargs)
        self.post_process()

    def pre_process(self, page_data, **kwargs):
        pass

    def do_process_page(self, page_data, **kwargs):
        self.to_pickle(page_data, **kwargs)

    def post_process(self):
        pass

    @abc.abstractmethod
    def export(self):
        pass

    @property
    def export_data(self) -> pd.DataFrame:
        try:
            data_frame = pd.DataFrame(columns=self._header)
            for data in self.read_pickle():
                data_frame = pd.concat(
                    [data_frame, pd.DataFrame(data, columns=self._header)]
                )
            return data_frame
        finally:
            self.remove_pickle()

    def to_pickle(self, obj, **kwargs):
        with open(self._pickle_file_name, self._mode) as f:
            pickle.dump(obj, f)

        if self._header is None:
            self._header = kwargs.get("header")

    def read_pickle(self):
        with open(self._pickle_file_name, "rb") as f:
            while True:
                try:
                    yield pickle.load(f)
                except EOFError:
                    break
        self.remove_pickle()

    def remove_pickle(self):
        if os.path.exists(self._pickle_file_name):
            os.remove(self._pickle_file_name)
