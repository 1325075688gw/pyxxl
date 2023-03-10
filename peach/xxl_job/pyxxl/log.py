# Author  : Gavin-GZ
# Time    : 2023/2/6 17:52


import logging
import sys
import os

from peach.helper.singleton.singleton import singleton_decorator
from peach.xxl_job.pyxxl.model import XxlJobLog, XxlJobInfo  # type: ignore
import pytz
from django.conf import settings

print(settings.SETTINGS_MODULE)


_srcfile = os.path.normcase(logging.addLevelName.__code__.co_filename)

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0


# class XxlJobFilter(logging.Filter):
#     def filter(self, record) -> bool:
#         from peach.xxl_job.pyxxl.ctx import g2
#
#         xxl_data = g2.xxl_run_data
#         trace_id = xxl_data.get("trace_id", None)
#         if not trace_id:
#             trace_id = trace_logging.get_trace_id()
#         if not trace_id:
#             trace_id = "".join(str(uuid.uuid4()).split("-"))
#         record.trace_id = trace_id
#         return True


@singleton_decorator
class XxlJobLogger(logging.Logger):
    def __init__(self, name):
        self.logger = self.getLogger(name)
        self.logger.level = INFO
        self.level = INFO
        self.setLevel(INFO)
        self.logger.setLevel(INFO)
        # self.logger.filters = [XxlJobFilter()]
        super().__init__(name, INFO)

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

    # def filter(self, record) -> bool:
    #     from peach.xxl_job.pyxxl.ctx import g2
    #     xxl_data = g2.xxl_run_data
    #     trace_id = xxl_data.get("trace_id", None)
    #     if not trace_id:
    #         trace_id = trace_logging.get_trace_id()
    #     if not trace_id:
    #         trace_id = "".join(str(uuid.uuid4()).split("-"))
    #     record.trace_id = trace_id
    #     return True

    def info(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g, g2

        xxl_kwargs = g2.xxl_run_data
        trace_id = xxl_kwargs.get("trace_id", None)
        kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(INFO, msg, args, **kwargs)},
                append=True,
            )
        log_id = xxl_kwargs.get("run_data", {}).get("logId", "")
        if log_id:
            msg = "logId: " + str(log_id) + "\n" + msg
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g, g2

        xxl_kwargs = g2.xxl_run_data
        trace_id = xxl_kwargs.get("trace_id", None)
        kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(WARNING, msg, args, **kwargs)},
                append=True,
            )
        log_id = xxl_kwargs.get("run_data", {}).get("logId", "")
        if log_id:
            msg = "logId: " + str(log_id) + "\n" + msg
        self.logger.warning(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g, g2

        xxl_kwargs = g2.xxl_run_data
        trace_id = xxl_kwargs.get("trace_id", None)
        kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(ERROR, msg, args, **kwargs)},
                append=True,
            )
        log_id = xxl_kwargs.get("run_data", {}).get("logId", "")
        if log_id:
            msg = "logId: " + str(log_id) + "\n" + msg
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.error(msg, *args, exc_info=True, **kwargs)

    def debug(self, msg, *args, **kwargs):
        from peach.xxl_job.pyxxl.ctx import g, g2

        xxl_kwargs = g2.xxl_run_data
        trace_id = xxl_kwargs.get("trace_id", None)
        kwargs.pop("trace_id", None)
        if trace_id:
            g.set_xxl_run_data(
                trace_id,
                {"handle_log": self._log(DEBUG, msg, args, **kwargs)},
                append=True,
            )
        log_id = xxl_kwargs.get("run_data", {}).get("logId", "")
        if log_id:
            msg = "logId: " + str(log_id) + "\n" + msg
        self.logger.debug(msg, *args, **kwargs)


async def prepare_handle_log(trace_id, id, handle_duration):
    from peach.xxl_job.pyxxl.ctx import g

    data = g.get_xxl_run_data(trace_id=trace_id)
    handle_log = data.get("handle_log")
    if len(handle_log) > 50000:
        handle_log = (
            handle_log[:20000]
            + "\n     The log exceeds the specified length(65535 chars)\n     ......\n     "
            + handle_log[len(handle_log) - 20000 :]
        )
    xxl_job_log = await get_xxl_job_log(id)
    xxl_job_log.handle_time = xxl_job_log.handle_time.astimezone(pytz.timezone("UTC"))
    handle_log_str = '<span style="color: black; font-weight:600">??????log:</span>'
    execute_status = "??????" if int(xxl_job_log.handle_code) == 200 else "??????"
    executor_log_params = (
        f"{'????????????  ':10}: {xxl_job_log.author} \n"
        f"{'????????????  ':10}: {xxl_job_log.trigger_time} \n"
        f"{'????????????  ':10}: {xxl_job_log.trigger_code} \n"
        f"{'??????????????? ':9}: {xxl_job_log.executor_address} \n"
        f"{'??????handler ':11}: {xxl_job_log.executor_handler} \n"
        f"{'?????????????????????':8}: {xxl_job_log.executor_param if xxl_job_log.executor_param else '???????????????'} \n"
        f"{'????????????  ':10}: {xxl_job_log.handle_time} \n"
        f"{'????????????  ':10}: {execute_status} \n"
        f"{'????????????  ':10}: {handle_duration} s\n"
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
