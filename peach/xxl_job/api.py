import asyncio
import json
import logging
import time

from peach.xxl_job.pyxxl import ExecutorConfig, PyxxlRunner
from peach.xxl_job.pyxxl.ctx import g
from peach.xxl_job.pyxxl.utils import setup_logging
from peach.xxl_job.pyxxl.job_info import JobInfo
import dataclasses

setup_logging(logging.DEBUG)

config = ExecutorConfig(
    # xxl_admin_baseurl="http://localhost:8080/xxl-job-admin/api/",
    # executor_app_name="xxl-job-python-executor-sample",
    # executor_host="127.0.0.1",
)

app = PyxxlRunner(config)

# app.run_executor()
