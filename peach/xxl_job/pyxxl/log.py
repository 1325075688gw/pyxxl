# Author  : Gavin-GZ
# Time    : 2023/2/6 17:52

# type: ignore

from django.db import models

import logging
import sys
import os
from peach.helper.singleton.singleton import singleton_decorator

_srcfile = os.path.normcase(logging.addLevelName.__code__.co_filename)

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

logger = object
logger_name = ""


def set_logger_name(name):
    global logger
    global logger_name
    logger_name = name
    logger = logging.getLogger(name)


@singleton_decorator
class XxlJobLogger(logging.Logger, logger):
    def __init__(self, level=WARNING):
        global logger_name
        super().__init__(logger_name, level)

    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
    ):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        sinfo = None
        if _srcfile:
            # IronPython doesn't track Python frames, so findCaller raises an
            # exception on some versions of IronPython. We trap it here so that
            # IronPython can use logging.
            try:
                fn, lno, func, sinfo = self.findCaller(stack_info, stacklevel)
            except ValueError:  # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else:  # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(
            self.name, level, fn, lno, msg, args, exc_info, func, extra, sinfo
        )
        return record

    @staticmethod
    def getLogger(name):
        return logging.getLogger(name)

    def info(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(INFO, msg, args, **kwargs)},
                append=True,
            )
        super().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(WARNING, msg, args, **kwargs)},
                append=True,
            )
        super().warning(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(trace_id, {"handle_log": msg}, append=True)
        super().warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(ERROR, msg, args, **kwargs)},
                append=True,
            )
        super().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        # from peach.xxl_job.pyxxl.ctx import g
        # g.set_xxl_run_data(kwargs["trace_id"], {"handle_log": msg})
        self.error(msg, *args, exc_info=True, **kwargs)

    def debug(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(DEBUG, msg, args, **kwargs)},
                append=True,
            )
        super().debug(msg, *args, **kwargs)


class XxlJobLog(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True)
    job_group = models.IntegerField(help_text="执行器主键ID")
    job_id = models.IntegerField(help_text="任务主键ID")
    executor_address = models.CharField(max_length=255, help_text="执行器地址，本次执行的地址")
    executor_handler = models.CharField(max_length=255, help_text="执行器任务handler")
    executor_param = models.CharField(max_length=128, help_text="执行器任务参数")
    executor_sharding_param = models.CharField(
        max_length=32, help_text="执行器任务分片参数，格式如 1/2"
    )
    executor_fail_retry_count = models.IntegerField(help_text="失败重试次数")
    trigger_time = models.DateTimeField(help_text="调度-时间")
    trigger_code = models.IntegerField(help_text="调度-结果")
    trigger_msg = models.TextField(help_text="调度-日志")
    handle_time = models.DateTimeField(help_text="执行-时间")
    handle_code = models.IntegerField(help_text="执行-状态")
    handle_msg = models.TextField(help_text="执行-日志")
    alarm_status = models.SmallIntegerField(help_text="告警状态：0-默认、1-无需告警、2-告警成功、3-告警失败")
    handle_log = models.TextField(help_text="执行日志：包括执行器地址、执行时间、执行状态、handler中的log输出")
    handle_duration = models.FloatField(help_text="执行时间，毫秒")

    class Meta:
        db_table = "xxl_job_log"


async def prepare_handle_log(trace_id, id, handle_duration):
    from peach.xxl_job.pyxxl.ctx import g

    data = g.get_xxl_run_data(trace_id=trace_id)
    handle_log = data.get("handle_log")
    xxl_job_log = await get_xxl_job_log(id)
    executor_log_params = (
        f"执行器地址: {xxl_job_log.executor_address} \n"
        f"执行handler: {xxl_job_log.executor_handler} \n"
        f"执行器任务参数: {xxl_job_log.executor_param} \n"
        f"调度时间: {xxl_job_log.trigger_time} \n"
        f"调度结果: {xxl_job_log.trigger_code} \n"
        f"执行时间: {xxl_job_log.handle_time} \n"
        f"执行状态: {xxl_job_log.handle_code} \n"
        f"执行耗时: {handle_duration} s\n"
        f"执行log: \n"
        f"{handle_log}"
    )
    print(executor_log_params)

    return executor_log_params


async def update_xxl_job_log(trace_id, id, handle_duration):
    handle_log = await prepare_handle_log(
        trace_id=trace_id, id=id, handle_duration=handle_duration
    )
    print(handle_log)
    XxlJobLog.objects.using("xxl_job").filter(id=id).update(
        handle_log=handle_log, handle_duration=handle_duration
    )


async def get_xxl_job_log(id):
    res = XxlJobLog.objects.using("xxl_job").filter(id=id)
    return res[0]


async def update_xxl_job_handle_time(id, handle_time):
    XxlJobLog.objects.using("xxl_job").filter(id=id).update(handle_time=handle_time)
