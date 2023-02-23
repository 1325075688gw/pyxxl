# type: ignore
import logging

from aiohttp import web

from peach.xxl_job.pyxxl import error
from peach.xxl_job.pyxxl.schema import RunData
import uuid
from peach.xxl_job.pyxxl.log import get_xxl_job_log
from peach.xxl_job.pyxxl.define import XXL_JOB_HANDLER_NOT_FOUND
from asgiref.sync import sync_to_async
from django.conf import settings
from peach.sender.slack_sender.slack_sender import send_slack_msg
from peach.sender.slack_sender.slack_helper import (
    get_slack_id_by_username,
    format_slack_user_id_list,
)
from peach.xxl_job.pyxxl.ctx import g2


logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


@routes.post("/beat")
async def beat(request: web.Request) -> web.Response:
    trace_id = "".join(str(uuid.uuid4()).split("-"))
    g2.set_xxl_run_data({"trace_id": trace_id})
    logger.debug("beat")
    return web.json_response(dict(code=200, msg=None))


@routes.post("/idleBeat")
async def idle_beat(request: web.Request) -> web.Response:
    trace_id = "".join(str(uuid.uuid4()).split("-"))
    g2.set_xxl_run_data({"trace_id": trace_id})
    data = await request.json()
    job_id = data["jobId"]
    logger.debug("idleBeat: %s" % data)
    if await request.app["executor"].is_running(data["jobId"]):
        return web.json_response(dict(code=500, msg="job %s is running." % job_id))
    return web.json_response(dict(code=200, msg=None))


@routes.post("/run")
async def run(request: web.Request) -> web.Response:
    """
        {
        "jobId":1,                                  // 任务ID
        "executorHandler":"demoJobHandler",         // 任务标识
        "executorParams":"demoJobHandler",          // 任务参数
        "executorBlockStrategy":"COVER_EARLY",      // 任务阻塞策略，可选值参考 com.xxl.job.core.enums.ExecutorBlockStrategyEnum
        "executorTimeout":0,                        // 任务超时时间，单位秒，大于零时生效
        "logId":1,                                  // 本次调度日志ID
        "logDateTime":1586629003729,                // 本次调度日志时间
        "glueType":"BEAN",                          // 任务模式，可选值参考 com.xxl.job.core.glue.GlueTypeEnum
        "glueSource":"xxx",                         // GLUE脚本代码
        "glueUpdatetime":1586629003727,             // GLUE脚本更新时间，用于判定脚本是否变更以及是否需要刷新
        "broadcastIndex":0,                         // 分片参数：当前分片
        "broadcastTotal":0                          // 分片参数：总分片
    }
    """
    data = await request.json()
    data["traceID"] = "".join(str(uuid.uuid4()).split("-"))
    g2.set_xxl_run_data({"trace_id": data["traceID"], "run_data": data})
    run_data = RunData(**data)
    logger.debug(
        "Get task request. jobId={} logId={} [{}]".format(
            run_data.jobId, run_data.logId, run_data
        )
    )
    try:
        await request.app["executor"].run_job(run_data)
    except error.JobDuplicateError as e:
        return web.json_response(dict(code=500, msg=e.message))
    except error.JobNotFoundError as e:
        im_id = await sync_to_async(get_slack_id_by_username)(username=run_data.author)
        format_im_id = format_slack_user_id_list([im_id])
        msg = XXL_JOB_HANDLER_NOT_FOUND.format(format_im_id, run_data.executorHandler)
        channel = settings.IM["slack"]["xxl-job"]["channel"]
        await sync_to_async(send_slack_msg)(channel=channel, text=msg)
        return web.json_response(dict(code=500, msg=e.message))

    return web.json_response(dict(code=200, msg=None))


@routes.post("/kill")
async def kill(request: web.Request) -> web.Response:
    trace_id = "".join(str(uuid.uuid4()).split("-"))
    g2.set_xxl_run_data({"trace_id": trace_id})
    data = await request.json()
    await request.app["executor"].cancel_job(data["jobId"])
    return web.json_response(dict(code=200, msg=None))


# todo
@routes.post("/log")
async def log(request: web.Request) -> web.Response:
    """
        {
        "logDateTim":0,     // 本次调度日志时间
        "logId":0,          // 本次调度日志ID
        "fromLineNum":0     // 日志开始行号，滚动加载日志
    }
    """
    trace_id = "".join(str(uuid.uuid4()).split("-"))
    g2.set_xxl_run_data({"trace_id": trace_id})
    data = await request.json()
    # logger.info("log %s" % data)
    xxl_job_log = await get_xxl_job_log(data["logId"])
    handle_log = xxl_job_log.handle_log
    if not handle_log:
        from peach.xxl_job.pyxxl.ctx import g

        handle_log = g.get_xxl_run_data_log_id(data["logId"]).get("handle_log", "")
    response = {
        "code": 200,
        "msg": None,
        "content": {
            "fromLineNum": 1,
            "toLineNum": 1,
            "logContent": handle_log,
            "isEnd": True if xxl_job_log.handle_log else False,
        },
    }

    return web.json_response(response)


def create_app() -> web.Application:
    """
    xxl_admin_k8s_baseurl xxl调度中心的接口地址，如http://localhost:8080/xxl-job-admin/api/
    executor_names 执行器名称列表
    executor_baseurl 执行器http接口的地址 如http://172.17.0.1:9999
    """
    app = web.Application()
    app.add_routes(routes)
    return app
