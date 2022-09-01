# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
import logging
import signal
import threading
import time

from django import db

from peach.misc import dt

from peach.timer import store

_LOGGER = logging.getLogger(__name__)

# 空闲时线程休眠时间（秒）
second_of_wait_task = 1
# 任务处理器
handler_map = {}
# 结束任务信号通道
shutdown_signal = False
is_running = False
# 最大并发线程数
workers_count = 10
# 批量获取任务数
batch_tasks = 4


def kill_task_when_signal(signum, frame):
    send_shutdown_signal()


def register_handler(task_handler):
    handler_map[task_handler.get_biz_code()] = task_handler


def send_shutdown_signal():
    _LOGGER.info("Timer service is shutdowing")
    global shutdown_signal, is_running
    shutdown_signal = True
    is_running = False


def run():

    _LOGGER.info("Timer is starting")

    signal.signal(signal.SIGINT, kill_task_when_signal)
    signal.signal(signal.SIGTERM, kill_task_when_signal)

    threads_pool = ThreadPoolExecutor(workers_count)
    limter = threading.Semaphore(workers_count)

    while not shutdown_signal:
        undo_tasks = store.get_engine().get_undo_tasks(batch_tasks)
        tasks_size = len(undo_tasks)

        if tasks_size > 0:
            _LOGGER.info("get undo tasks size: %s" % tasks_size)

        if not tasks_size:
            time.sleep(second_of_wait_task)
            continue

        for task in undo_tasks:
            # put the task back on it's shutdowning
            if shutdown_signal:
                store.get_engine().retry_task(task.biz_code, task.biz_num)
                continue

            limter.acquire()
            threads_pool.submit(handle_task, task, limter)

    threads_pool.shutdown()
    _LOGGER.info("Timer Has been shutdowned")


def handle_task(task, limiter: threading.Semaphore):
    ts = dt.now_mts()
    try:
        db.close_old_connections()
        task_info = f"{task.biz_code} - {task.biz_num}"
        _LOGGER.info(f"start processing the timer task: {task_info}")
        if task.biz_code not in handler_map:
            raise Exception(f"the biz code invalid: {task.biz_code}")
        next_time = handler_map.get(task.biz_code).handle(task)
        if next_time:
            # 再次执行此任务
            _LOGGER.info(f"reschedule the task: {task_info}")
            store.get_engine().retry_task(task.biz_code, task.biz_num, next_time)
        else:
            # 标识此任务已完成
            store.get_engine().finished_task(task.biz_code, task.biz_num)
    except Exception:
        _LOGGER.exception(f"processing failed: {task_info}")
    finally:
        _LOGGER.info(f"finished the task: {task_info} in {dt.now_mts() - ts} ms")
        limiter.release()
