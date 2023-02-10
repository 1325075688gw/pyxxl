# Author  : Gavin-GZ
# Time    : 2023/2/7 16:32

import logging

from telegram import TelegramError
from django.conf import settings
from peach.sender.telegram_sender.telegram_client import TelegramBot

_LOGGER = logging.getLogger(__name__)

telegramBot = TelegramBot()


def send_telegram_msg(chat_id: str, text: str) -> None:
    """发送 telegram 消息"""
    if not settings.IM["telegram"]["xxl-job"]["token"]:
        _LOGGER.warning("telegram token is empty")
        return

    _LOGGER.info("send telegram msg, chat_id: %s, text: %s", chat_id, text)

    try:
        telegramBot.send_message(chat_id=chat_id, text=text)
    except TelegramError:
        _LOGGER.exception("send telegram message error")
