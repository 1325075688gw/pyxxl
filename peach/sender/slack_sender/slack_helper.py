# Author  : Gavin-GZ
# Time    : 2023/2/7 20:43

from peach.misc.redis import ProxyAgent
import logging
from slack_sdk.errors import SlackApiError
from django.conf import settings
from peach.sender.slack_sender.define import SLACK_USER_LIST
from peach.sender.slack_sender.slack_client import slack_client
import traceback

_LOGGER = logging.getLogger(__name__)
redis_client = ProxyAgent(url=settings.REDIS_URL)


def get_slack_user_list() -> list:
    """获取 slack 用户列表"""
    user_list = []
    try:
        response = slack_client.users_list()
        if response["ok"]:
            user_list = response["members"]
    except SlackApiError:
        # 处理错误
        _LOGGER.exception("get slack user list error")
    except Exception:
        _LOGGER.error(traceback.format_exc())
    return user_list


def update_user_list_cache():
    """缓存用户名与ID的映射关系"""
    user_list = get_slack_user_list()
    _LOGGER.info("get user list count: %d", len(user_list))
    for item in user_list:
        if "real_name" in item and item["real_name"]:
            redis_client.client.hset(SLACK_USER_LIST, item["real_name"], item["id"])
    # 必须添加该语句，创建SLACK_USER_LIST hmap对象
    redis_client.client.hset(
        SLACK_USER_LIST,
        "e10adc3949ba59abbe56e057f20f883e",
        "e10adc3949ba59abbe56e057f20f883e",
    )


def get_slack_id_by_username(username, index=0):
    exist_status = redis_client.client.exists(SLACK_USER_LIST)
    update_user_list_cache_flag = False
    if not exist_status:
        update_user_list_cache()
        update_user_list_cache_flag = True
    # 这儿不能get_slack_id_by_username，会出现死循环
    slack_user_id = redis_client.client.hget(SLACK_USER_LIST, username)
    if not slack_user_id and not update_user_list_cache_flag and (index == 0):
        update_user_list_cache()
        # 不可以可以调用get_slack_id_by_username，会出现死循环
        slack_user_id = redis_client.client.hget(SLACK_USER_LIST, username)
    # 不管能否获取slack_user_id，都需要有返回值
    return slack_user_id if slack_user_id else username


def get_slack_user_id_list_by_username_list(username_list):
    slack_user_id_list = []
    for index in range(len(username_list)):
        slack_user_id = get_slack_id_by_username(username_list[index], index)
        slack_user_id_list.append(slack_user_id)
    return slack_user_id_list


def format_slack_user_id_list(user_id_list=None):
    if not user_id_list:
        return ""
    slack_user_id_list = ",".join(["<@{}>".format(user_id) for user_id in user_id_list])
    return slack_user_id_list
