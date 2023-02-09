# Author  : Gavin-GZ
# Time    : 2023/2/9 16:20
# type: ignore

from django.db import models


class XxlJobLog(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True)
    job_group = models.IntegerField(help_text="执行器主键ID")
    job_id = models.IntegerField(help_text="任务主键ID")
    executor_address = models.CharField(max_length=256, help_text="执行器地址，本次执行的地址")
    executor_handler = models.CharField(max_length=256, help_text="执行器任务handler")
    executor_param = models.CharField(max_length=128, help_text="执行器任务参数")
    executor_sharding_param = models.CharField(
        max_length=32, help_text="执行器任务分片参数，格式如 1/2"
    )
    executor_fail_retry_count = models.IntegerField(help_text="失败重试次数")
    trigger_time = models.DateTimeField(help_text="调度-时间")
    trigger_code = models.IntegerField(help_text="调度-结果")
    trigger_msg = models.TextField(help_text="调度-日志")
    handle_time = models.DateTimeField(help_text="执行-时间")
    handle_code = models.IntegerField(help_text="执行-状态")
    handle_msg = models.TextField(help_text="执行-日志")
    alarm_status = models.SmallIntegerField(help_text="告警状态：0-默认、1-无需告警、2-告警成功、3-告警失败")
    handle_log = models.TextField(help_text="执行日志：包括执行器地址、执行时间、执行状态、handler中的log输出")
    handle_duration = models.FloatField(help_text="执行时间，秒")

    class Meta:
        db_table = "xxl_job_log"


class XxlJobInfo(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True)
    job_group = models.IntegerField(help_text="执行器主键ID")
    job_desc = models.CharField(max_length=256, help_text="任务描述")
    add_time = models.DateTimeField(help_text="创建时间")
    update_time = models.DateTimeField(help_text="更新时间")
    author = models.CharField(max_length=64, help_text="作者")
    alarm_email = models.CharField(max_length=256, help_text="报警邮件")
    schedule_type = models.CharField(max_length=128, help_text="调度类型")
    schedule_conf = models.CharField(max_length=128, help_text="cron表达式")
    misfire_strategy = models.CharField(max_length=128, help_text="调度过期策略")
    executor_route_strategy = models.CharField(max_length=128, help_text="执行器路由策略")
    executor_handler = models.CharField(max_length=128, help_text="执行器")
    executor_param = models.CharField(max_length=128, help_text="执行参数")
    executor_block_strategy = models.CharField(max_length=128, help_text="执行参数")
    executor_timeout = models.IntegerField(help_text="任务执行超时时间，单位秒")
    executor_fail_retry_count = models.IntegerField(help_text="失败重试次数")
    glue_type = models.CharField(max_length=128, help_text="GLUE类型")
    glue_source = models.TextField(max_length=128, help_text="GLUE源代码")
    glue_remark = models.CharField(max_length=128, help_text="GLUE备注")
    glue_updatetime = models.DateTimeField(help_text="GLUE更新时间")
    child_jobid = models.CharField(max_length=128, help_text="子任务ID，多个逗号分隔")
    trigger_status = models.IntegerField(help_text="调度状态：0-停止，1-运行")
    trigger_last_time = models.BigIntegerField(help_text="上次调度时间")
    trigger_next_time = models.BigIntegerField(help_text="下次调度时间")
    dynamic_add = models.IntegerField(help_text="0-非动态添加，1-动态添加")

    class Meta:
        db_table = "xxl_job_info"
