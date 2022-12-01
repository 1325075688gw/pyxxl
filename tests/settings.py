import pymysql

INSTALLED_APPS = [
    "peach.timer",
    "peach.admin",
]

DB_AES_KEY = "ZmtkZiomZmQ4NzZmZGZLZg=="

SAFE_DOG_CONFIG = {
    "api_domain": "x",
    "app_key": "x",
    "app_secret": "x",
}

REPORT_CONG = {
    "server_host": "xx",
    "app_key": "xx",
    "app_secret": "xxx",
    "temp_file_dir": "xxx",
    "debug": "xxx",
}

USE_TZ = True
pymysql.install_as_MySQLdb()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "test_peach",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
    }
}

MEMCACHED_ENABLE = True
MEMCACHED_URL = "127.0.0.1:11211"

try:
    from .settings_local import *  # noqa: F403 F401
except Exception:
    pass
