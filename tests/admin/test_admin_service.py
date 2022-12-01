import pytest
from django.conf import settings

from peach.admin.models import User, Token
from peach.admin.services import admin_service
from peach.misc.exceptions import BizException


@pytest.mark.django_db(transaction=True)
def test_login_by_token(mocker):
    name, is_super = "aaaa", True

    mocker.patch.object(settings, "LOGIN_BY_TOKEN_ENABLE", create=True, new=False)
    with pytest.raises(BizException):
        admin_service.login_by_token(name, is_super)

    mocker.patch.object(settings, "LOGIN_BY_TOKEN_ENABLE", create=True, new=True)
    user_info = admin_service.login_by_token(name, is_super)

    user = User.objects.filter(name=name, is_super=True).first()
    assert user is not None
    assert user.id == user_info["id"]

    token = (
        Token.objects.filter(token=user_info["token"]).select_related("user").first()
    )
    assert token is not None
    assert token.user.id == user_info["id"]

    user_2 = admin_service.login_by_token(name, is_super)
    assert user_2["id"] == user.id


@pytest.mark.django_db(transaction=True)
def test_login_by_token_with_duplicate_name():
    User.objects.create(
        name="user-1",
        password="xxxxx",
        enable=False,
    )

    User.objects.create(name="user-2", password="xxxx", deleted=True)

    with pytest.raises(BizException):
        admin_service.login_by_token("user-1", False)

    with pytest.raises(BizException):
        admin_service.login_by_token("user-2", False)


@pytest.mark.django_db(transaction=True)
def test_login_by_password(mocker):
    name, pwd = "user-1", "Pp111111"
    admin_service.add_user(name=name, password=pwd, enable=True, is_super=True)

    admin_service.login(name=name, password=pwd)

    mocker.patch.object(settings, "LOGIN_BY_PASSWORD_ENABLE", create=True, new=False)
    with pytest.raises(BizException):
        admin_service.login(name=name, password=pwd)
