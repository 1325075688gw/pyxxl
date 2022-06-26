from django.conf import settings

from .kafka import init, close, log

__all__ = ["init", "close", "log"]

init(settings.MAESTRO_KAFKA_BROKER_SERVERS, settings.MAESTRO_ENABLE)
