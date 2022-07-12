# -*- coding: utf-8 -*-
import importlib
import logging
import signal

from django.conf import settings
from django.core.management.base import BaseCommand

from peach.timer.api import run as run_task, shutdown, register_handler

_LOGGER = logging.getLogger(__name__)


def kill_task_when_signal(signum, frame):
    shutdown()


class Command(BaseCommand):
    help = "Start task command."

    def handle(self, *args, **options):

        if hasattr(settings, "TASK_HANDLERS") and settings.TASK_HANDLERS:
            for handler in settings.TASK_HANDLERS:
                mod_path, sep, cls_name = handler.rpartition(".")
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name)()
                register_handler(cls)

                _LOGGER.info("registry success handler: {}".format(cls))
        else:
            _LOGGER.info("project has no any task handlers")

        run_task()
        signal.signal(signal.SIGINT, kill_task_when_signal)
        signal.signal(signal.SIGTERM, kill_task_when_signal)
        self.stdout.write("task启动成功......")
