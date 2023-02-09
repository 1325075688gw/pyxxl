# type: ignore
import asyncio
import datetime
import functools
import json
import time
import dataclasses

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional
from json import JSONDecodeError
from pytz import timezone
from asgiref.sync import sync_to_async


import requests

from peach.xxl_job.pyxxl import error
from peach.xxl_job.pyxxl.ctx import g
from peach.xxl_job.pyxxl.enum import executorBlockStrategy
from peach.xxl_job.pyxxl.schema import HandlerInfo, RunData
from peach.xxl_job.pyxxl.setting import ExecutorConfig
from peach.xxl_job.pyxxl.types import DecoratedCallable
from peach.xxl_job.pyxxl.xxl_client import XXL
from peach.xxl_job.pyxxl import log
from peach.xxl_job.pyxxl.log import XxlJobLogger
from peach.sender.slack_sender.slack_sender import send_slack_msg
from django.conf import settings
from peach.xxl_job.pyxxl.define import XXL_JOB_EXECUTE_FAIL_MSG
from peach.sender.slack_sender.slack_helper import (
    get_slack_id_by_username,
    format_slack_user_id_list,
)
from peach.xxl_job.pyxxl.job_info import JobInfo

logger = XxlJobLogger(__name__)


class JobHandler:
    _handlers: Dict[str, HandlerInfo] = {}

    @classmethod
    def dynamic_register(cls, job_info: JobInfo):
        cookies = {"REMOTE_COOKIE": ExecutorConfig.remote_cookie}
        if type(job_info.executorHandler) != str:
            handler = job_info.executorHandler.__class__(job_info.executorHandler)
            handler_name = handler.value  # type: ignore
            job_info.executorHandler = handler_name
        job_info = dataclasses.asdict(job_info)
        res = requests.post(
            url=ExecutorConfig().xxl_admin_k8s_baseurl + "jobinfo/add_by_dynamic/",
            data=job_info,
            cookies=cookies,
        )
        return json.loads(res.text)

    def register(
        self, *args: Any, name: Optional[str] = None, replace: bool = False
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """将函数注册到可执行的job中,如果其他地方要调用该方法,replace修改为True"""

        def func_wrapper(func: DecoratedCallable) -> DecoratedCallable:
            handler_name = name or func.__name__
            if type(handler_name) != str:
                handler = handler_name.__class__(handler_name)
                handler_name = handler.value  # type: ignore
            if handler_name in self._handlers and replace is False:
                raise error.JobRegisterError(
                    "handler %s already registered." % handler_name
                )
            self._handlers[handler_name] = HandlerInfo(handler=func)
            logger.info(
                "register job {},is async: {}".format(
                    handler_name, asyncio.iscoroutinefunction(func)
                )
            )

            @functools.wraps(func)
            def inner_wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            return inner_wrapper

        if len(args) == 1:
            return func_wrapper(args[0])

        return func_wrapper

    def get(self, name: str) -> Optional[HandlerInfo]:
        return self._handlers.get(name, None)

    def handlers_info(self) -> List[str]:
        return [
            "<{} is_async:{}>".format(k, v.is_async) for k, v in self._handlers.items()
        ]


class Executor:
    def __init__(
        self,
        xxl_client: XXL,
        config: ExecutorConfig,
        *,
        handler: Optional[JobHandler] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """执行器，真正的调度任务和策略都在这里

        Args:
            xxl_client (XXL): xxl客户端
            config (ExecutorConfig): 配置参数
            handler (Optional[JobHandler], optional): Defaults to None.
            loop (Optional[asyncio.AbstractEventLoop], optional): Defaults to None.
        """

        self.xxl_client = xxl_client
        self.config = config

        self.handler: JobHandler = handler or JobHandler()
        self.loop = loop or asyncio.get_event_loop()
        self.tasks: Dict[int, asyncio.Task] = {}
        self.queue: Dict[int, List[RunData]] = defaultdict(list)
        self.lock = asyncio.Lock()
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="pyxxl_pool",
        )

    async def shutdown(self) -> None:
        for _, task in self.tasks.items():
            task.cancel()

    async def run_job(self, run_data: RunData) -> None:
        handler_obj = self.handler.get(run_data.executorHandler)
        if not handler_obj:
            logger.warning("handler %s not found." % run_data.executorHandler)
            raise error.JobNotFoundError(
                "handler %s not found." % run_data.executorHandler
            )

        # 一个执行器同时只能执行一个jobId相同的任务
        async with self.lock:
            current_task = self.tasks.get(run_data.jobId)
            if current_task:
                # 不用的阻塞策略
                # pylint: disable=no-else-raise
                if (
                    run_data.executorBlockStrategy
                    == executorBlockStrategy.DISCARD_LATER.value
                ):
                    raise error.JobDuplicateError(
                        "The same job [%s] is already executing and this has been discarded."
                        % run_data.jobId
                    )
                elif (
                    run_data.executorBlockStrategy
                    == executorBlockStrategy.COVER_EARLY.value
                ):
                    logger.warning(
                        "job {} is  COVER_EARLY, logId {} replaced.".format(
                            run_data.jobId, run_data.logId
                        )
                    )
                    await self._cancel(run_data.jobId)
                elif (
                    run_data.executorBlockStrategy
                    == executorBlockStrategy.SERIAL_EXECUTION.value
                ):

                    if len(self.queue[run_data.jobId]) >= self.config.task_queue_length:
                        msg = (
                            "job {job_id} is  SERIAL, queue length more than {max_length}."
                            "logId {log_id}  discard!".format(
                                job_id=run_data.jobId,
                                log_id=run_data.logId,
                                max_length=self.config.task_queue_length,
                            )
                        )
                        logger.error(msg)
                        raise error.JobDuplicateError(msg)
                    else:
                        queue = self.queue[run_data.jobId]
                        logger.info(
                            "job {job_id} is in queen, logId {log_id} ranked {ranked}th [max={max_length}]...".format(
                                job_id=run_data.jobId,
                                log_id=run_data.logId,
                                ranked=len(queue) + 1,
                                max_length=self.config.task_queue_length,
                            )
                        )
                        queue.append(run_data)
                        return
                else:
                    raise error.JobParamsError(
                        "unknown executorBlockStrategy [%s]."
                        % run_data.executorBlockStrategy,
                        executorBlockStrategy=run_data.executorBlockStrategy,
                    )

            start_time = int(time.time()) * 1000
            task = self.loop.create_task(self._run(handler_obj, start_time, run_data))
            self.tasks[run_data.jobId] = task

    async def cancel_job(self, job_id: int) -> None:
        async with self.lock:
            await self._cancel(job_id)

    async def is_running(self, job_id: int) -> bool:
        return job_id in self.tasks

    async def _send_slack_msg(self, msg):
        channel = settings.IM["slack"]["xxl-job"]["channel"]
        await sync_to_async(send_slack_msg)(channel=channel, text=msg)

    async def _prepare_slack_msg(self, handler, author, log_id):
        log_url = settings.XXL_JOB[
            "xxl_admin_web_baseurl"
        ] + "joblog/logDetailPage?id={}".format(log_id)
        im_id = await sync_to_async(get_slack_id_by_username)(username=author)
        format_im_id = format_slack_user_id_list([im_id])
        msg = XXL_JOB_EXECUTE_FAIL_MSG.format(
            cron_task_name=handler, status="失败", im_uid=format_im_id, log_url=log_url
        )
        return msg

    async def _run(self, handler: HandlerInfo, start_time: int, data: RunData) -> None:
        handle_time = datetime.datetime.now(tz=timezone("Asia/Shanghai"))
        try:
            task_status = True
            if data.executorParams:
                data.executorParams = json.loads(data.executorParams)
                if type(data.executorParams) == str:
                    data.executorParams = json.loads(data.executorParams)
            g.set_xxl_run_data(data.traceID, {"xxl_kwargs": data})
            start_job = '<span style="color: red;">Start job</span>'
            logger.info(
                "{} jobId={} logId={} [{}]".format(
                    start_job, data.jobId, data.logId, data
                ),
                trace_id=data.traceID,
            )
            func = (
                handler.handler(data.traceID)
                if handler.is_async
                else self.loop.run_in_executor(
                    self.thread_pool, handler.handler, data.traceID
                )
            )
            handle_time = datetime.datetime.now(tz=timezone("Asia/Shanghai"))
            await log.update_xxl_job_handle_time(data.logId, handle_time)
            result = await asyncio.wait_for(
                func, data.executorTimeout or self.config.task_timeout
            )
            finish_job = '<span style="color: red;">Job finished</span>'
            logger.info(
                f"{finish_job} jobId={data.jobId} logId={data.logId}",
                trace_id=data.traceID,
            )
            await self.xxl_client.callback(data.logId, start_time, code=200, msg=result)
        except asyncio.CancelledError as e:
            task_status = False
            logger.warning(e, exc_info=True, trace_id=data.traceID)
            await self.xxl_client.callback(
                data.logId, start_time, code=500, msg="CancelledError"
            )
        except JSONDecodeError:
            task_status = False
            logger.exception(msg="参数格式错误，期望json字符串", trace_id=data.traceID)
            await self.xxl_client.callback(
                data.logId, start_time, code=500, msg="参数格式错误，期望json字符串"
            )
        except Exception as err:  # pylint: disable=broad-except
            task_status = False
            logger.exception(err, trace_id=data.traceID)
            await self.xxl_client.callback(
                data.logId, start_time, code=500, msg=str(err)
            )
        finally:
            handle_duration = (
                time.time() * 1000 - handle_time.timestamp() * 1000
            ) / 1000
            handle_duration = format(handle_duration, ".4f")
            await log.update_xxl_job_log(data.traceID, data.logId, handle_duration)
            g.delete_xxl_run_data(data.traceID)
            if task_status:
                await self._finish(data.jobId)
            else:
                msg = await self._prepare_slack_msg(
                    data.executorHandler, data.author, data.logId
                )
                await self._send_slack_msg(msg)

    async def _finish(self, job_id: int) -> None:
        self.tasks.pop(job_id, None)
        # 如果有队列中的任务，开始执行队列中的任务
        queue = self.queue[job_id]
        if queue:
            kwargs: RunData = queue.pop(0)
            logger.info(
                "JobId {} in queue[{}], start job with logId {}".format(
                    kwargs.jobId, len(queue), kwargs.logId
                )
            )
            await self.run_job(kwargs)

    async def _cancel(self, job_id: int) -> None:
        task = self.tasks.pop(job_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.warning("Job %s cancelled." % job_id)

    async def graceful_close(self, timeout: int = 60) -> None:
        """优雅关闭"""

        async def _graceful_close() -> None:
            while len(self.tasks) > 0:
                await asyncio.wait(self.tasks.values())

        await asyncio.wait_for(_graceful_close(), timeout=timeout)

    def reset_handler(self, handler: JobHandler) -> None:
        self.handler = handler
