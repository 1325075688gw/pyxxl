# Author  : Gavin-GZ
# Time    : 2023/2/6 17:52

# type: ignore


import logging
import sys
import os
from peach.helper.singleton.singleton import singleton_decorator
from logging import getLogger
from peach.xxl_job.pyxxl.model import XxlJobLog, XxlJobInfo
import pytz

_srcfile = os.path.normcase(logging.addLevelName.__code__.co_filename)

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0


@singleton_decorator
class XxlJobLogger(logging.Logger):
    def __init__(self, name):
        self.logger = getLogger(name)
        super().__init__(name, DEBUG)

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
    def getLogger(logger_name):
        return logging.getLogger(logger_name)

    def info(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(INFO, msg, args, **kwargs)},
                append=True,
            )
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(WARNING, msg, args, **kwargs)},
                append=True,
            )
        self.logger.warning(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(trace_id, {"handle_log": msg}, append=True)
        self.logger.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g

        trace_id = kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(ERROR, msg, args, **kwargs)},
                append=True,
            )
        self.logger.error(msg, *args, **kwargs)

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
        self.logger.debug(msg, *args, **kwargs)


async def prepare_handle_log(trace_id, id, handle_duration):
    from peach.xxl_job.pyxxl.ctx import g

    data = g.get_xxl_run_data(trace_id=trace_id)
    handle_log = data.get("handle_log")
    xxl_job_log = await get_xxl_job_log(id)
    xxl_job_log.handle_time = xxl_job_log.handle_time.astimezone(pytz.timezone("UTC"))
    handle_log_str = '<span style="color: black; font-weight:600">执行log:</span>'
    executor_log_params = (
        f"任务归属        : {xxl_job_log.author} \n"
        f"调度时间        : {xxl_job_log.trigger_time} \n"
        f"调度结果        : {xxl_job_log.trigger_code} \n"
        f"执行器地址      : {xxl_job_log.executor_address} \n"
        f"执行handler    : {xxl_job_log.executor_handler} \n"
        f"执行器任务参数   : {xxl_job_log.executor_param if xxl_job_log.executor_param else '参数为空！'} \n"
        f"执行时间        : {xxl_job_log.handle_time} \n"
        f"执行状态        : {'成功' if xxl_job_log.handle_code == 200 else '失败'} \n"
        f"执行耗时        : {handle_duration} s\n"
        f"{handle_log_str} \n"
        f"{handle_log}"
    )

    return executor_log_params


async def update_xxl_job_log(trace_id, id, handle_duration):
    handle_log = await prepare_handle_log(
        trace_id=trace_id, id=id, handle_duration=handle_duration
    )
    XxlJobLog.objects.using("xxl_job").filter(id=id).update(
        handle_log=handle_log, handle_duration=handle_duration
    )


async def get_xxl_job_log(id):
    res = XxlJobLog.objects.using("xxl_job").filter(id=id)
    return res[0]


async def update_xxl_job_handle_time(id, handle_time):
    XxlJobLog.objects.using("xxl_job").filter(id=id).update(handle_time=handle_time)


async def delte_xxl_job_info(id):
    XxlJobInfo.objects.using("xxl_job").filter(id=id).delete()
