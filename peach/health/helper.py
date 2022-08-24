from django.conf import settings
from django.http import HttpResponseServerError


def check_mysql():
    if settings.DATABASES.get("default", {}).get("HOST"):
        # 只有配置了mysql,才检查
        from django.db import connections

        for name in connections:
            cursor = connections[name].cursor()
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row is None:
                return HttpResponseServerError("db: invalid response")
