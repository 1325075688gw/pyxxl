import importlib
import os
import signal
from threading import Barrier
import logging
from django.conf import settings

from django.core.management import BaseCommand

from peach.kafka import consumer

_LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "start kafka consumer"

    def handle(self, *args, **options):

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        for app in settings.INSTALLED_APPS:
            try:
                importlib.import_module(app + ".kafka_listener")
            except ModuleNotFoundError:
                pass

        counter = Barrier(len(consumer.listener_container) + 1)
        for group_id, _ in consumer.listener_container.items():
            procesor = consumer.ProcessorThread(
                group_id, settings.KAFKA_BOOTSTRAP_SERVERS, counter
            )
            procesor.start()

        counter.wait()
        _LOGGER.info("kafka exited in main processor")


def handle_signal(signalnum, frame):
    pid = os.getpid()
    _LOGGER.info(
        "consumer process {} receives signal {}, sets exit flag".format(pid, signalnum)
    )
    consumer.shutdown = True
