from django.conf import settings

from .client import ReportClient

report_client = ReportClient(**settings.REPORT_CONG)
report_decorator = report_client.decorator()
