import pytest
from django.conf import settings
from django.utils import timezone
from mongoengine import disconnect_all, connect


@pytest.fixture(scope="session")
def mongo_mock():
    """
    pytest mongo mock 服务
    用法:
    def test_xx(mongo_mock):
        ....
    """
    print("\n>>> init mongo mock...\n")
    disconnect_all()
    for db in settings.MONGODB_DATABASES:
        connect(
            db,
            alias=db,
            host="mongomock://localhost",
            tz_aware=True,
            tzinfo=timezone.get_current_timezone(),
            connect=False,
        )
