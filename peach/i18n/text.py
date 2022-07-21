import csv
import logging
import os
import typing


_LOGGER = logging.getLogger(__name__)


class I18NException(Exception):
    pass


class ResouceLoader:
    def __init__(self, path: str) -> None:
        if not os.path.isfile(path):
            raise ValueError(f"The languages resource does not seem to exist: {path}")

        # {[msg_id]: {[lan]: [text]}}
        self._texts: typing.Dict[str, typing.Dict[str, str]] = {}
        # {[col_num]: [lan]}
        self._headers: typing.Dict[int, str] = {}

        first_row = True
        with open(path, "r") as f:
            reader = csv.reader(f, delimiter=",")
            row_num = -1
            for row in reader:
                row_num += 1
                if first_row:
                    self._parse_headers(row)
                    first_row = False
                else:
                    self._parse_texts(row_num, row)

        _LOGGER.info("Load i18n resource success")

    def _parse_headers(self, headers: typing.List[str]):
        self._check_headers_format(headers)
        for col_num in range(2, len(headers)):
            self._headers[col_num] = headers[col_num].strip()

    def _check_headers_format(self, headers: typing.List[str]):
        if len(headers) <= 3 and headers[:3] != ["Module", "msg_id", "zh"]:
            raise I18NException(
                "The languages resource file has invalid format data, the headers must contains: Module, msg_id, zh"
            )

    def _parse_texts(self, row_num: int, row: typing.List[str]):
        if len(row) - 2 != len(self._headers):
            raise I18NException(
                f"The data on {row_num} does not match the headers. row: {row}, headers: {self._headers}"
            )
        msg_id = row[1].strip()
        if msg_id in self._texts:
            raise I18NException(f"The msg_id in row {row_num} is duplicated")
        self._texts[msg_id] = lans = {}
        for col_num in range(2, len(row)):
            lans[self._headers[col_num]] = row[col_num].strip()

    def get_text(self, msg_id, lan, **kwargs) -> str:
        if msg_id not in self._texts:
            _LOGGER.warning(f"i18n, the msg_id is not exists: {msg_id}")
            return msg_id
        lans = self._texts[msg_id]
        if lan not in lans:
            _LOGGER.warning(f"i18n, the lan is not exists: {lan} in msg_id: {msg_id}")
            return msg_id
        text = lans[lan]
        return text.format(**kwargs) if kwargs else text

    def get_all_lans(self) -> typing.Set[str]:
        return set(self._headers.values())

    # just for debug
    def print_all(self):
        print(f"headers: {self._headers}")
        print(f"texts: {self._texts}")
