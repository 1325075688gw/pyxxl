import asyncio
import logging
import time

from peach.xxl_job.pyxxl import ExecutorConfig, PyxxlRunner
from peach.xxl_job.pyxxl.ctx import g
from peach.xxl_job.pyxxl.utils import setup_logging

setup_logging(logging.DEBUG)

config = ExecutorConfig(
    # xxl_admin_k8s_baseurl="http://localhost:8080/xxl-job-admin/api/",
    executor_app_name="xxl-job-python-executor-sample",
    # executor_host="127.0.0.1",
)

app = PyxxlRunner(config)


@app.handler.register(name="demoJobHandler")
async def _test_task():
    # you can get task params with "g"
    print("get executor params: %s" % g.xxl_run_data.executorParams)
    await asyncio.sleep(5)
    return "成功..."


@app.handler.register(name="test_task3")
async def _test_task3():
    await asyncio.sleep(3)
    return "成功3"


@app.handler.register(name="test_task4")
def _test_task4():
    time.sleep(3)
    return "成功3"


job_info = {
    "appname": "xxl-job-python-executor-sample",
    "jobDesc": "粉sss孙菲菲身份",
    "author": "龚伟2233333222a",
    "alarmEmail": "1325075688@qq.com",
    "scheduleType": "CRON",
    "scheduleConf": "1-2 * 3,4,18,23 * * ?",
    "cronGen_display": "1-2 * * * * ?",
    "schedule_conf_CRON": "",
    "schedule_conf_FIX_RATE": "",
    "schedule_conf_FIX_DELAY": "",
    "glueType": "BEAN",
    "executorHandler": "demoJobHandler",
    "executorParam": "123",
    "executorRouteStrategy": "FAILOVER",
    "childJobId": "",
    "misfireStrategy": "DO_NOTHING",
    "executorBlockStrategy": "SERIAL_EXECUTION",
    "executorTimeout": 0,
    "executorFailRetryCount": 0,
    "glueRemark": "GLUE代码初始化",
    "glueSource": "",
}

# app.handler.dynamic_register(job_info)
app.run_executor()
