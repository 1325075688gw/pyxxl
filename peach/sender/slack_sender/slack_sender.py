# Author  : Gavin-GZ
# Time    : 2023/2/7 16:32


import logging
from io import IOBase
from typing import Union, Sequence
from slack_sdk.errors import SlackApiError
from peach.sender.slack_sender.slack_client import SlackClient

_LOGGER = logging.getLogger(__name__)

slack_client = SlackClient()


def send_slack_msg(channel: str, text: str) -> None:
    """发送 slack 消息"""
    _LOGGER.info("send slack msg, channel: %s, text: %s", channel, text)

    try:
        slack_client.chat_postMessage(channel=channel, text=text)
    except SlackApiError:
        # You will get a SlackApiError if "ok" is False
        # assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        _LOGGER.exception("send slack message error")


def send_slack_img(
    channels: Union[str, Sequence[str]], file: Union[str, bytes, IOBase], filename: str
) -> None:

    _LOGGER.info("send slack img, channels: %s, filename: %s", channels, filename)
    try:
        slack_client.files_upload(channels=channels, file=file, filename=filename)
    except SlackApiError:
        # You will get a SlackApiError if "ok" is False
        # assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        _LOGGER.exception("send slack img error")
