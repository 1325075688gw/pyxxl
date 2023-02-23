from dataclasses import dataclass
from django.conf import settings


@dataclass
class JobInfo:
    jobDesc: str
    author: str
    alarmEmail: str
    executorHandler: str
    executorParam: str
    scheduleConf: str = "0 15 10 * * ? 2005"
    triggerNextTime: int = 0
    scheduleType: str = "CRON"
    appname: str = ""
    cronGen_display: str = ""
    schedule_conf_CRON: str = ""
    schedule_conf_FIX_RATE: str = ""
    schedule_conf_FIX_DELAY: str = ""
    glueType: str = "BEAN"
    executorRouteStrategy: str = "ROUND"
    childJobId: str = ""
    misfireStrategy: str = "FIRE_ONCE_NOW"
    executorBlockStrategy: str = "COVER_EARLY"
    executorTimeout: int = 0
    executorFailRetryCount: int = 0
    glueRemark: str = "GLUE代码初始化"
    glueSource: str = ""
    uniqueKey: str = ""

    def __post_init__(self):
        self.cronGen_display = self.scheduleConf
        self.appname = settings.XXL_JOB["appname"]

    # def __init__(self):


# job_info_demo
# job_info = JobInfo(jobDesc="复读是风沙大发", author="sss", alarmEmail="fff", scheduleConf="0 0 0 * * ? *", executorHandler="dd", executorParam="fsd")

# app.handler.dynamic_register(job_info)
