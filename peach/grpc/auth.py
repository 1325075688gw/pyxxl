import grpc  # type: ignore

_SIGNATURE_HEADER_KEY = "x-signature"


class SignatureValidationInterceptor(grpc.ServerInterceptor):
    def __init__(self, token):

        self._token = token

        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid signature")

        self._abortion = grpc.unary_unary_rpc_method_handler(abort)

    def intercept_service(self, continuation, handler_call_details):
        expected_metadata = (_SIGNATURE_HEADER_KEY, self._token)
        if expected_metadata in handler_call_details.invocation_metadata:
            return continuation(handler_call_details)
        else:
            return self._abortion


class AuthHeader(grpc.AuthMetadataPlugin):
    def __init__(self, auth_token: str):
        self._auth_token = auth_token

    def __call__(self, context, callback):
        callback(((_SIGNATURE_HEADER_KEY, self._auth_token),), None)
