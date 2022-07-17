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

    def _parse_headers(self, row: typing.List[str]):
        if len(row) < 3:
            raise I18NException(
                "The languages resource must contains at least 3 languages"
            )
        if row[0].strip() != "msg_id":
            raise I18NException("The languages resource file has invalid format data")
        self._headers[0] = "-"
        for col_num in range(1, len(row)):
            self._headers[col_num] = row[col_num].strip()

    def _parse_texts(self, row_num: int, row: typing.List[str]):
        if len(row) != len(self._headers):
            raise I18NException(f"The Data on {row_num} is missing some languages")
        msg_id = row[0].strip()
        if msg_id in self._texts:
            raise I18NException(f"The msg_id in row {row_num} is duplicated")
        self._texts[msg_id] = lans = {}
        for col_num in range(1, len(row)):
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

    # for debug
    def print_all(self):
        print(f"headers: {self._headers}")
        print(f"texts: {self._texts}")
