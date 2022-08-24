import importlib
import logging

from django.apps import AppConfig
from django.conf import settings

from .api import gconf_client

_LOGGER = logging.getLogger(__name__)


class ConfConfig(AppConfig):
    name = "peach.gconf"

    def ready(self):
        """
        django settings 配置说明

        如果需要配置 bind dataclass, 配置如下：
        GCONF_DATACLASSES = {
            "facebook.toml": "core_account.conf.facebook_conf",
        }

        如果要配置 register callbacks, 配置如下：
        GCONF_CALLBACKS = {
            "server.toml": "core_account.conf.reload_conf",
        }

        """

        if hasattr(settings, "GCONF_DATACLASSES"):
            for name, handler in settings.GCONF_DATACLASSES.items():
                mod_path, sep, conf_name = handler.rpartition(".")
                mod = importlib.import_module(mod_path)
                conf_inst = getattr(mod, conf_name)
                gconf_client.bind_dataclass(name, conf_inst)

        if hasattr(settings, "GCONF_CALLBACKS"):
            for name, handler in settings.GCONF_CALLBACKS.items():
                mod_path, sep, callback_name = handler.rpartition(".")
                mod = importlib.import_module(mod_path)
                callback = getattr(mod, callback_name)
                gconf_client.register_callback(name, callback)

        start_conf()


def start_conf():
    gconf_client.start()
