# -*- coding: utf-8 -*-
import logging
import threading
import time

from django import db

from .api import report_client


class TaskProcessThread(threading.Thread):
    def __init__(self, shutdown_signal=False, second_of_wait_task=60):
        super().__init__()
        self.shutdown_signal = shutdown_signal
        self.second_of_wait_task = second_of_wait_task

    def stop(self):
        self.shutdown_signal = True

    def run(self):
        logging.info("start the report processor.....")
        while not self.shutdown_signal:
            report_client.load_cur_task()

            undo_tasks = report_client.cur_task
            if not undo_tasks:
                time.sleep(self.second_of_wait_task)
                continue

            db.close_old_connections()
            report_client.executor()
        else:
            logging.info("the task executor had shutdown")


task = TaskProcessThread()


def run():
    task.start()


def stop():
    task.stop()
