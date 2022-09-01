from django.utils import timezone

from . import store
from .executor import run, register_handler, send_shutdown_signal, handler_map


def add_task(biz_code, biz_num, when=None, biz_ext=None):
    """
    添加新任务
    :param biz_code: 任务执行处理器编码
    :param biz_num: 任务编码
    :param when: 定时时间, 为空时表示立即执行
    :param biz_ext: 业务自定义内容
    """
    store.get_engine().add_task(
        biz_code, biz_num, when if when else timezone.now(), biz_ext
    )


def cancel_task(biz_code, biz_num):
    """
    取消未执行的任务
    :param biz_code: 任务执行处理器编码
    :param biz_num: 任务编码
    :return:
    """
    store.get_engine().finished_task(biz_code, biz_num)


def get_tasks_by_code(biz_code=None, biz_num=None, when=None):
    """
    获取业务对应任务, biz_num为模糊查询
    :param biz_code: 任务类型
    :param biz_num: 任务编码
    :param when: 定时时间
    :return:
    """
    return store.get_engine().get_tasks_by_code(
        biz_code=biz_code, biz_num=biz_num, when=when
    )


def register_task_handler(task_handler):
    """
    注册任务处理器
    :param task_handler: 任务处理器
    :return:
    """
    register_handler(task_handler)


def get_task_handlers():
    return handler_map.values()


def start():
    """
    开启服务
    :return:
    """
    run()


def shutdown():
    """
    关闭服务
    :return:
    """
    send_shutdown_signal()


class TaskHandler:
    def handle(self, task):
        """
        子类必需重写此方法处理业务逻辑
        :param task:
        :return:
        """
        raise NotImplementedError("must ovrride process")

    def get_biz_code(self):
        """
        子类返回业务场景编码
        :return:
        """
        raise NotImplementedError("must override get_biz_code")
