import grpc

from .auth import AuthHeader
from .util import read_credential_file


def insecure_channel(host: str):
    return grpc.insecure_channel(host)


def secure_channel(host: str, credentials_ca_cert_path: str, auth_token: str):
    call_credentials = grpc.metadata_call_credentials(AuthHeader(auth_token))
    channel_credential = grpc.ssl_channel_credentials(
        read_credential_file(credentials_ca_cert_path)
    )
    composite_credentials = grpc.composite_channel_credentials(
        channel_credential, call_credentials
    )
    return grpc.secure_channel(host, composite_credentials)
