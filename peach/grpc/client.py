import grpc

from .auth import AuthHeader, _SIGNATURE_HEADER_KEY
from .inner import header_manipulator_client_interceptor
from .util import read_credential_file


def insecure_channel(host: str, auth_token: str):
    header_adder_interceptor = (
        header_manipulator_client_interceptor.header_adder_interceptor(
            _SIGNATURE_HEADER_KEY, auth_token
        )
    )
    intercept_channel = grpc.intercept_channel(
        grpc.insecure_channel(host), header_adder_interceptor
    )
    return intercept_channel


def secure_channel(host: str, credentials_ca_cert_path: str, auth_token: str):
    call_credentials = grpc.metadata_call_credentials(AuthHeader(auth_token))
    channel_credential = grpc.ssl_channel_credentials(
        read_credential_file(credentials_ca_cert_path)
    )
    composite_credentials = grpc.composite_channel_credentials(
        channel_credential, call_credentials
    )
    return grpc.secure_channel(host, composite_credentials)
