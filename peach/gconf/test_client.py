#! -*- coding:utf-8 -*-
import logging
import sys
import time

from .client import GConfClient

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)


def restart_redis(value):
    logging.info("========= callback" + value)


def test_a():
    logging.info("====== begin test")
    conf = GConfClient(
        "http://3.1.171.240:8881/",
        "YgLeBncBZSxXfrB5qJmvH-MEiKXlT75mxe-ByjQi",
        "kZOL3l1QZGf5N9LRbsm5C7W8i3AwZtOhBYxYIE89",
        "/tmp/pyconf/",
        full_pull_interval=20,
    )

    conf.register_callbacks({"cd": restart_redis})
    conf.start()

    while True:
        try:
            logging.info(conf.get_int("cd", 33))
        except Exception:
            logging.exception("get conf fail: {}".format("a"))
        time.sleep(5)


if __name__ == "__main__":
    test_a()
