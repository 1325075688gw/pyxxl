import importlib
import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .api import report_client

_LOGGER = logging.getLogger(__name__)


class ReportConfig(AppConfig):
    name = "peach.report"

    def ready(self):
        """
        django settings 配置说明

        class ReportType(Enum):
            ADMIN_RECORD = "admin_record"  # 操作纪录

        REPORT_TASK = {
            ReportType.ADMIN_RECORD.value: 'peach.admin.services.admin_service.export_record',
        }
        """
        if report_client is None:
            raise ImproperlyConfigured("The REPORT_CONG settings must not be empty.")

        if hasattr(settings, "REPORT_TASK") and settings.REPORT_TASK:
            for report_type, func_path in settings.REPORT_TASK.items():
                mod_path, sep, callback_name = func_path.rpartition(".")
                mod = importlib.import_module(mod_path)
                func = getattr(mod, callback_name)
                report_client.register(report_type, func)
                _LOGGER.info(f"registry report task: {report_type} - {func_path}")
