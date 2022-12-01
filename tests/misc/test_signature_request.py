import copy
from enum import Enum
from marshmallow import fields

from peach.django.forms import EnumField
from peach.misc.signature_request import (
    signature_params,
    SignRequestSchema,
)


class T(Enum):
    new = "new"
    old = "old"


def test_signature_request():
    secret_key = "fwndzm5_uh35-kg&93yny25nm&a!h5_dc5*l!=fn^"

    ori_params = {
        "name": "111111",
        "pwd": "Passwerd",
        "enum_list": [T.new.value],
        "e": T.new.value,
    }
    ori_params_copy = copy.copy(ori_params)
    params = signature_params(secret_key, ori_params)

    class TestSign(SignRequestSchema):
        name = fields.String(required=True)
        pwd = fields.String()
        enum_list = fields.List(EnumField(T))
        e = EnumField(T)

        def get_secret_key(self, *args, **kwargs):
            return secret_key

    res = TestSign().load(params)
    assert res["name"] == ori_params_copy["name"]
    assert res["pwd"] == ori_params_copy["pwd"]
    assert res["enum_list"][0].value == ori_params_copy["enum_list"][0]
    assert res["e"].value == ori_params_copy["e"]
