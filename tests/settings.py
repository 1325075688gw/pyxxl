import pymysql

INSTALLED_APPS = ["peach.timer"]

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
