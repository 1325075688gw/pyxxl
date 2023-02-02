from dataclasses import dataclass
from peach.xxl_job.pyxxl.config import yaml_config


@dataclass
class JobInfo:
    jobDesc: str
    author: str
    alarmEmail: str
    scheduleConf: str
    executorHandler: str
    executorParam: str
    scheduleType: str = "CRON"
    appname: str = ""
    cronGen_display: str = ""
    schedule_conf_CRON: str = ""
    schedule_conf_FIX_RATE: str = ""
    schedule_conf_FIX_DELAY: str = ""
    glueType: str = "BEAN"
    executorRouteStrategy: str = "FIRST"
    childJobId: str = ""
    misfireStrategy: str = "DO_NOTHING"
    executorBlockStrategy: str = "SERIAL_EXECUTION"
    executorTimeout: int = 0
    executorFailRetryCount: int = 0
    glueRemark: str = "GLUE代码初始化"
    glueSource: str = ""

    def __post_init__(self):
        self.cronGen_display = self.scheduleConf
        self.appname = yaml_config["appname"]

    # def __init__(self):


# job_info_demo
# job_info = JobInfo(jobDesc="复读是风沙大发", author="sss", alarmEmail="fff", scheduleConf="0 0 0 * * ? *", executorHandler="dd", executorParam="fsd")

# app.handler.dynamic_register(job_info)

