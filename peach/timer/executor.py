# -*- coding: utf-8 -*-
import logging
import threading
import time

from django import db

from peach.timer import store

_LOGGER = logging.getLogger(__name__)

# 空闲时线程休眠时间（秒）
second_of_wait_task = 1
# 任务处理器
handler_map = {}
# 结束任务信号通道
shutdown_signal = False
is_running = False


def register_handler(task_handler):
    handler_map[task_handler.get_biz_code()] = task_handler


def send_shutdown_signal():
    global shutdown_signal, is_running
    shutdown_signal = True
    is_running = False


class TaskProcessThread(threading.Thread):
    def run(self):
        _LOGGER.info("start the task processor.....")
        global is_running
        is_running = True
        while not shutdown_signal:
            undo_tasks = store.get_engine().get_undo_tasks()
            if len(undo_tasks) > 0:
                _LOGGER.info("get undotask size: %s" % len(undo_tasks))

            if not undo_tasks:
                time.sleep(second_of_wait_task)
                continue

            db.close_old_connections()  # 关闭数据库失效连接
            for task in undo_tasks:
                try:
                    _LOGGER.info("begin process the task: %s" % task)
                    if task.biz_code not in handler_map:
                        raise Exception(f"the biz code invalid: {task.biz_code}")
                    next_time = handler_map.get(task.biz_code).handle(task)
                    if next_time:
                        # 再次执行此任务
                        _LOGGER.info("retry the task: %s" % task)
                        store.get_engine().retry_task(
                            task.biz_code, task.biz_num, next_time
                        )
                    else:
                        # 标识此任务已完成
                        _LOGGER.info("finished the task: %s" % task)
                        store.get_engine().finished_task(task.biz_code, task.biz_num)
                except Exception:
                    _LOGGER.exception("fail process task: %s" % task)
        else:
            _LOGGER.info("the task executor had shutdown")


def run():
    if not is_running:
        for _ in range(4):
            TaskProcessThread().start()
    else:
        _LOGGER.info("task is running, not allow start again")
