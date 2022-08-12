import hmac
import json
import logging
from collections import OrderedDict
from hashlib import sha1
import requests


_LOGGER = logging.getLogger(__name__)


class SafeDogClient:
    def __init__(self, api_domain, app_key, app_secret):
        """
        :param api_domain: api主域名
        :param app_key: 接入平台的唯一标识
        :param app_secret: 平台自己的密钥，一定要安全保管，如有泄漏，及时找管理更改
        """
        self.api_domain = api_domain
        self.app_key = app_key
        self.app_secret = app_secret
        self.http_domain = api_domain

    def verify_token(self, user_id, token, ip):
        """
        验证用户的动态Token。
        :param user_id: 平台自己的用户唯一标识
        :param token: token是基于TOTP协议的设备产生的6位动态数字密码
        :param ip: 用户的请求ip， 非平台服务器ip
        :return: 如果验证通过返回True
        """
        data = {"app_key": self.app_key, "user_id": user_id, "token": token, "ip": ip}
        sorted_data = json.dumps(OrderedDict(sorted(data.items())))
        sign = self._encrypt_data(sorted_data)
        data["sign"] = sign

        return self._request("verify_token", data)

    def _request(self, uri, data):
        resp = requests.post(self.http_domain + "/" + uri, data=data)
        if resp.status_code != 200:
            _LOGGER.info("safe_dog response text: {}".format(resp.text))
            return False
        resp_json = json.loads(resp.content)
        return resp_json["status"] == 0

    def _encrypt_data(self, data):
        return hmac.new(
            self.app_secret.encode(), data.encode("utf-8"), sha1
        ).hexdigest()


safe_client: SafeDogClient = None
