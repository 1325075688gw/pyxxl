import base64
from .encrypt import AESCipher
from django.conf import settings

_AES = AESCipher(base64.b64decode(settings.DB_AES_KEY))


def db_encrypt(value: str) -> str:
    """DB数据加密"""
    if not value:
        return ""
    return base64.b64encode(_AES.encrypt(value.encode())).decode()


def db_decrypt(value: str) -> str:
    """DB数据解密"""
    if not value:
        return ""
    return _AES.decrypt(base64.b64decode(value)).decode()
