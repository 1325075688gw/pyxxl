# Author  : Gavin-GZ
# Time    : 2023/2/7 20:41

from slack_sdk import WebClient
from peach.helper.singleton.singleton import singleton_decorator
from django.conf import settings


@singleton_decorator
class SlackClient(WebClient):
    def __init__(self, token=settings.IM["slack"]["xxl-job"]["token"]):
        super().__init__(token=token)
