import typing
from asyncio import iscoroutinefunction
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class HandlerInfo:
    handler: Callable

    @property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.handler)


@dataclass(frozen=False)
class RunData:
    """
    调度器传入的所有参数，执行函数通过g来获取这些参数

    !!! example

        ```python
        from peach.xxl_job.pyxxl.ctx import g

        @xxxxx
        async def test():
            print(g.xxl_run_data.logId)
        ```

    """

    # 重要参数
    jobId: int
    logId: int
    executorHandler: str
    executorBlockStrategy: str
    traceID: str
    author: str
    dynamicAdd: int

    executorParams: Optional[typing.Any] = None
    executorTimeout: Optional[int] = None
    logDateTime: Optional[int] = None
    glueType: Optional[str] = None
    glueSource: Optional[str] = None
    glueUpdatetime: Optional[int] = None
    broadcastIndex: Optional[int] = None
    broadcastTotal: Optional[int] = None
