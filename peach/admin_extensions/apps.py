from django.apps import AppConfig


class AdminExtensionsConfig(AppConfig):
    name = "peach.admin_extensions"

    def ready(self) -> None:
        from . import receiver  # noqa
