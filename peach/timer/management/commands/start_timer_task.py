# -*- coding: utf-8 -*-
import importlib
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from peach.timer.api import start, register_handler

_LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Start task command."

    def handle(self, *args, **options):

        if hasattr(settings, "TASK_HANDLERS") and settings.TASK_HANDLERS:
            for handler in settings.TASK_HANDLERS:
                mod_path, sep, cls_name = handler.rpartition(".")
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name)()
                register_handler(cls)

                _LOGGER.info("[timer]registry success handler: {}".format(cls))
        else:
            _LOGGER.info("[timer]Has no any task handlers")

        start()
