import importlib
import logging
from django.conf import settings

from django.core.management import BaseCommand

from peach.kafka import consumer

_LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "starting kafka consumer"

    def handle(self, *args, **options):

        for app in settings.INSTALLED_APPS:
            try:
                importlib.import_module(app + ".kafka_listener")
            except ModuleNotFoundError:
                pass

        consumer.start_consumer(settings.KAFKA_BOOTSTRAP_SERVERS)
