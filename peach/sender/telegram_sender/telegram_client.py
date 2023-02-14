# Author  : Gavin-GZ
# Time    : 2023/2/8 02:17

import logging

import telegram
from peach.helper.singleton.singleton import singleton_decorator
from django.conf import settings

_LOGGER = logging.getLogger(__name__)


@singleton_decorator
class TelegramBot(telegram.Bot):
    def __init__(self, token):
        super().__init__(token=token)


telegram_bot = TelegramBot(token=settings.settings.IM["telegram"]["xxl-job"]["token"])
