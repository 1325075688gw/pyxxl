import asyncio
import logging

from fastapi import FastAPI

from peach.xxl_job.pyxxl import JobHandler
from peach.xxl_job.pyxxl.utils import setup_logging


setup_logging(logging.DEBUG)


app = FastAPI()
xxl_handler = JobHandler()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@xxl_handler.register(name="demoJobHandler")
async def test_task():
    await asyncio.sleep(10)
    return "成功10"
