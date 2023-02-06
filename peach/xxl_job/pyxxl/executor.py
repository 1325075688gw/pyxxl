import asyncio
import functools
import json
import logging
import time
import dataclasses

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional
from json import JSONDecodeError

import requests

from peach.xxl_job.pyxxl import error
from peach.xxl_job.pyxxl.ctx import g
from peach.xxl_job.pyxxl.enum import executorBlockStrategy
from peach.xxl_job.pyxxl.schema import HandlerInfo, RunData
from peach.xxl_job.pyxxl.setting import ExecutorConfig
from peach.xxl_job.pyxxl.types import DecoratedCallable
from peach.xxl_job.pyxxl.xxl_client import XXL

logger = logging.getLogger(__name__)


class JobHandler:
    _handlers: Dict[str, HandlerInfo] = {}

    @classmethod
    def dynamic_register(cls, job_info):
        cookies = {"REMOTE_COOKIE": ExecutorConfig.remote_cookie}
        job_info = dataclasses.asdict(job_info)
        res = requests.post(
            url=ExecutorConfig().xxl_admin_baseurl + "jobinfo/add_by_dynamic/",
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
                handler_name = handler_name.value
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

    async def _run(self, handler: HandlerInfo, start_time: int, data: RunData) -> None:
        try:
            if data.executorParams:
                data.executorParams = json.loads(data.executorParams)
                if type(data.executorParams) == str:
                    data.executorParams = json.loads(data.executorParams)
            g.set_xxl_run_data(data)
            logger.info(
                "Start job jobId={} logId={} [{}]".format(data.jobId, data.logId, data)
            )
            func = (
                handler.handler(data.traceID)
                if handler.is_async
                else self.loop.run_in_executor(
                    self.thread_pool, handler.handler, data.traceID
                )
            )
            result = await asyncio.wait_for(
                func, data.executorTimeout or self.config.task_timeout
            )
            g.delete_xxl_run_data(data.traceID)
            logger.info("Job finished jobId={} logId={}".format(data.jobId, data.logId))
            await self.xxl_client.callback(data.logId, start_time, code=200, msg=result)
        except asyncio.CancelledError as e:
            logger.warning(e, exc_info=True)
            await self.xxl_client.callback(
                data.logId, start_time, code=500, msg="CancelledError"
            )
        except JSONDecodeError as e:
            logger.exception(e)
            await self.xxl_client.callback(
                data.logId, start_time, code=500, msg="参数格式错误，期望json字符串"
            )
        except Exception as err:  # pylint: disable=broad-except
            logger.exception(err)
            await self.xxl_client.callback(
                data.logId, start_time, code=500, msg=str(err)
            )
        finally:
            await self._finish(data.jobId)

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
