import logging

from django.apps import AppConfig

from . import store

_LOGGER = logging.getLogger(__name__)


class TaskConfig(AppConfig):
    name = "peach.timer"

    def ready(self):
        from .store.mysql import MySqlTaskStore

        store.set_engine(MySqlTaskStore())
