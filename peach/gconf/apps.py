import logging

from django.apps import AppConfig

from .api import gconf_client

_LOGGER = logging.getLogger(__name__)


class ConfConfig(AppConfig):
    name = "peach.gconf"

    def ready(self):
        try:
            import uwsgidecorators

            @uwsgidecorators.postfork
            def execute_after_startup():
                start_conf()

        except ModuleNotFoundError:
            start_conf()


def start_conf():
    gconf_client.start()
