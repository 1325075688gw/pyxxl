from django.conf import settings

from .client import ReportClient

if hasattr(settings, "REPORT_CONG"):
    report_client = ReportClient(**settings.REPORT_CONG)
else:
    report_client = None
report_decorator = ReportClient.decorator
