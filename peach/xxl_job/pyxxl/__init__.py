import importlib.metadata

from peach.xxl_job.pyxxl.executor import JobHandler  # type: ignore
from peach.xxl_job.pyxxl.main import PyxxlRunner
from peach.xxl_job.pyxxl.setting import ExecutorConfig


def help():
    m = importlib.metadata
    j = JobHandler
    p = PyxxlRunner
    e = ExecutorConfig
    return m, j, p, e


# __version__ = importlib.metadata.version("pyxxl")
