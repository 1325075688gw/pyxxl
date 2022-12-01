import enum
import hashlib

from marshmallow import validates_schema, post_load
from peach.django.forms import BaseSchema, fields


from . import dt


def signature_params(secret_key: str, params: dict) -> dict:
    """计算签名
    计算之后，params中新增`sign`和`timestamp`字段

    :param str secret_key: _description_
    :param dict params: _description_
    :return dict: _description_
    """
    params["timestamp"] = int(dt.now_ts())

    s = ""
    for k in sorted(params.keys()):
        if params[k] is not None:
            s += "{}={}&".format(k, params[k])
    s += "key=%s" % secret_key
    m = hashlib.md5()
    m.update(s.encode("utf-8"))
    sign = m.hexdigest().upper()
    params["sign"] = sign
    return params


class SignRequestSchema(BaseSchema):
    timestamp = fields.Integer(required=True)
    sign = fields.String(required=True)

    def get_secret_key(self, *args, **kwargs):
        raise NotImplementedError()

    @validates_schema
    def check_signature(self, data, **kwargs):
        c_data = data.copy()
        sign = c_data.pop("sign")
        s = ""
        for k in sorted(c_data.keys()):
            rs = c_data[k]
            if (
                c_data[k]
                and isinstance(c_data[k], list)
                and isinstance(c_data[k][0], enum.Enum)
            ):
                rs = [e.value for e in c_data[k]]

            if c_data[k] and isinstance(c_data[k], enum.Enum):
                rs = c_data[k].value
            if rs is not None:
                s += "{}={}&".format(k, rs)
        s += "key=%s" % self.get_secret_key(data)
        m = hashlib.md5()
        m.update(s.encode("utf-8"))
        if sign.upper() != m.hexdigest().upper():
            raise ValueError("signature error")

    @post_load
    def remove_sign_params(self, data, **kwargs):
        del data["timestamp"]
        del data["sign"]
        return data
