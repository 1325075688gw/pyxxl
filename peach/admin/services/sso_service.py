import logging
import requests
import json
from dataclasses import dataclass

from django.conf import settings
from peach.misc.signature_request import signature_params
from peach.misc.exceptions import BizException
from peach.admin.exceptions import ERROR_SSO_CALLBACK_FAILED

from peach.misc import retry, util

_LOGGER = logging.getLogger(__name__)


@util.singleton
class SSOClient:
    def __init__(self) -> None:
        self.conf = settings.SSO_CONF
        self.headers = {"content-type": "application/json"}

    @property
    def secret_key(self):
        return self.conf["secret_key"]

    @property
    def verify_token_url(self):
        return self.conf["host"] + self.conf["verify_token_uri"]

    @property
    def verify_vcode_url(self):
        return self.conf["host"] + self.conf["verify_vcode_uri"]

    def verify_token(self, code: str):
        url = self.verify_token_url
        data = {"code": code}
        _LOGGER.info(f"sso callback: url={url}, data={data}")
        data = signature_params(self.secret_key, data)
        return self._do_post(url=url, data=data, headers=self.headers)

    def verify_vcode(self, username: str, vcode: str):
        url = self.verify_vcode_url
        data = {
            "username": username,
            "vcode": vcode,
        }
        _LOGGER.info(f"sso callback: url={url}, data={data}")
        data = signature_params(self.secret_key, data)
        return self._do_post(url=url, data=data, headers=self.headers)

    def _do_post(self, url, data, headers, timeout=5):
        dumps_data = json.dumps(data)
        resp = requests.post(url, data=dumps_data, headers=headers, timeout=timeout)
        try:
            resp_json = resp.json()
        except Exception:
            _LOGGER.error(
                f"sso callback error: request url={url}, params={data}, res_text={resp.text}"
            )
            raise
        if not resp.ok:
            raise BizException(
                ERROR_SSO_CALLBACK_FAILED,
                message=f"sso callback error:status={resp_json['status']}, msg={resp_json['msg']}",
            )
        return resp_json["data"]


@dataclass
class VerifyTokenDto:
    username: str
    is_super: bool


@retry.retry(requests.RequestException)
def verify_token(code: str) -> VerifyTokenDto:
    client = SSOClient()
    res_data = client.verify_token(code=code)
    return VerifyTokenDto(**res_data)


@retry.retry(requests.RequestException)
def verify_vcode(username: str, vcode: str) -> bool:
    client = SSOClient()
    res_data = client.verify_vcode(username=username, vcode=vcode)
    return res_data["status"] is True


if __name__ == "__main__":
    """
    # settings.py
    SSO_CONF = {
        "host": ENV["sso"]["host"],
        "secret_key": ENV["sso"]["secret_key"],
        "verify_token_uri": ENV["sso"]["verify_token"]["uri"],
        "verify_vcode_uri": ENV["sso"]["verify_vcode"]["uri"],
    }
    SSO_VERIFY_VCODE_ENABLE = ENV["sso"]["verify_vcode"]["enable"]
    # 兼容不需要sso的版本
    LOGIN_BY_PASSWORD_ENABLE = ENV["sso"]["verify_token"]["enable_login_by_password"]
    LOGIN_BY_TOKEN_ENABLE = ENV["sso"]["verify_token"]["enable_login_by_token"]

    # env.yaml
    sso:
        host: "http://127.0.0.1:8000"
        secret_key: "ZmtkZiomZmQ4NzZ"
        verify_token:
            uri: "/callback/verify_token/"
            enable_login_by_token: false
            enable_login_by_password: false
        verify_vcode:
            uri: "/callback/verify_v_code/"
            enable: true
    """
