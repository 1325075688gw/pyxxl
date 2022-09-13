import inspect
import typing
from abc import abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor

import grpc

from .auth import SignatureValidationInterceptor
from .util import read_credential_file


class BaseServer:
    def __init__(self, listen_address: str, max_workers: int = 5):
        """
        :param listen_address: the address and port used for the server
        :param max_workers: the max numbers of threads to execute tasks
        """
        self._listen_address = listen_address
        self._max_workers = max_workers
        self._server = None
        self.init_server()

    def register_service(self, service):
        """
        register the class of the implement service
        :param service: the implement for the interface defined in proto file
        """
        assert inspect.isclass(service)

        rpc_interface_cls = service.mro()[1]
        getattr(
            inspect.getmodule(rpc_interface_cls),
            f"add_{rpc_interface_cls.__name__}_to_server",
        )(service(), self._server)

    def startup(self):
        self._server.start()
        self._server.wait_for_termination()

    @abstractmethod
    def init_server(self):
        pass


class SecureServer(BaseServer):
    """
    Secure tunnel encrypted data with RSA and provide client authenticate by token
    """

    def __init__(
        self,
        listen_address: str,
        credentials_pair_paths: typing.Tuple,
        auth_token: str,
        max_workers=5,
    ):
        """
        :param credentials_pair_paths: (key_path, crt_path)
        :param auth_token: token used by authentication
        """
        self._credentials_pair_paths = credentials_pair_paths
        self._auth_token = auth_token
        super().__init__(listen_address, max_workers)

    def init_server(self):
        self._server = grpc.server(
            ThreadPoolExecutor(max_workers=self._max_workers),
            interceptors=[SignatureValidationInterceptor(self._auth_token)],
        )
        server_credentials = grpc.ssl_server_credentials(
            ((tuple(read_credential_file(p) for p in self._credentials_pair_paths)),)
        )
        self._server.add_secure_port(self._listen_address, server_credentials)


class InSecureServer(BaseServer):
    """
    Insecure tunnel, the data transmitted by the tunnel has risk of leakage
    """

    def init_server(self):
        self._server = grpc.server(ThreadPoolExecutor(max_workers=self._max_workers))
