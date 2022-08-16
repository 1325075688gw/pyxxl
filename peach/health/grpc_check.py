import logging

from peach.health.helper import check_mysql
from peach.health.pb import health_pb2_grpc, health_pb2

logger = logging.getLogger("healthz")


class HealthCheckService(health_pb2_grpc.HealthServicer):
    """
    提供健康检查 GRPC 接口
    测试方法:
    grpc_health_probe -addr mala-core-grpc:50051 \
        -tls \
        --tls-ca-cert /path/to/mala-core-grpc.crt \
        -tls-server-name=mala-core-grpc \
        -rpc-header=x-signature:{认证token}
    """

    def Check(self, request, context):
        try:
            check_mysql()
        except Exception as e:
            logger.exception(e)
            return health_pb2.HealthCheckResponse(
                status=health_pb2.HealthCheckResponse.ServingStatus.NOT_SERVING
            )
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.ServingStatus.SERVING
        )
