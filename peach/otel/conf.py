from dataclasses import dataclass


@dataclass
class TraceConf:
    enable: bool = False
    service_name: str = None
    endpoint_host: str = None  # OTel collector receiver 地址
    endpoint_port: int = None
    enable_grpc_client: bool = False  # 是否启用 grpc client 自动检测
    enable_grpc_server: bool = False  # 是否启用 grpc server 自动检测
    debug: bool = False
