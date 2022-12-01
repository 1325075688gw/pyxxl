from django.apps import AppConfig
from django.conf import settings

from peach.admin import safe_dog


class AdminConfig(AppConfig):
    name = "peach.admin"

    def ready(self) -> None:

        if (not settings.DEBUG) and hasattr(settings, "SAFE_DOG_CONFIG"):
            safe_dog.safe_client = safe_dog.SafeDogClient(**settings.SAFE_DOG_CONFIG)
