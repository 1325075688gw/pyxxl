import logging

from django.http import HttpResponse, HttpResponseServerError
from peach.health.helper import check_mysql

logger = logging.getLogger("healthz")


class HealthCheckMiddleware:
    """提供健康检查 HTTP 接口"""

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if request.method == "GET":
            if request.path == "/inner/readiness":
                return self.readiness(request)
            elif request.path == "/inner/healthz":
                return self.healthz(request)
        return self.get_response(request)

    def healthz(self, request):
        """
        Returns that the server is alive.
        """
        return HttpResponse("OK")

    def readiness(self, request):
        # Connect to each database and do a generic standard SQL query
        # that doesn't write any data and doesn't depend on any tables
        # being present.
        try:
            check_mysql()
        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError("db: cannot connect to database.")

        return HttpResponse("OK")
