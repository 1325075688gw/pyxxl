# Author  : Gavin-GZ
# Time    : 2023/2/7 15:27

from django.conf import settings
from peach.misc.env import ENV


settings = settings

IM = {
    "slack": {
        "xxl-job": {
            "token": ENV["im"]["slack"]["xxl-job"]["token"],
            "channel": ENV["im"]["slack"]["xxl-job"]["channel"],
        }
    },
    "telegram": {
        "xxl-job": {
            "token": ENV["im"]["telegram"]["xxl-job"]["token"],
            "channel": ENV["im"]["telegram"]["xxl-job"]["channel"],
        }
    },
}

REDIS_URL = ENV["redis"]["url"]


settings.IM = IM
settings.REDIS_URL = REDIS_URL


def test_send_slack_msg():
    from peach.sender.slack_sender.slack_sender import send_slack_msg
    from peach.sender.slack_sender.slack_helper import (
        get_slack_user_id_list_by_username_list,
        format_slack_user_id_list,
    )

    user_id_list = get_slack_user_id_list_by_username_list(["ALin", "gavin"])
    format_user_id_list = format_slack_user_id_list(user_id_list)
    print("format_user_id_list", format_user_id_list)
    msg = "定时任务【{cron_task_name}】执行【{status}】 {im_uid}, 任务执行日志: ({log_url})"
    work_sys_channel = settings.IM["slack"]["work_sys_channel"]
    text = msg.format(
        cron_task_name="撒哈拉沙漠",
        status="success",
        im_uid=format_user_id_list,
        log_url="http://www.baidu.com",
    )
    send_slack_msg(work_sys_channel, text)


def test_get_slack_id_by_username():
    from peach.sender.slack_sender.slack_helper import get_slack_id_by_username

    user_id = get_slack_id_by_username("gavin")
    print(user_id)


def test_get_slack_user_id_list_by_username_list():
    from peach.sender.slack_sender.slack_helper import (
        get_slack_user_id_list_by_username_list,
    )

    user_id_list = get_slack_user_id_list_by_username_list(["gavin", "ALin"])
    print(user_id_list)
