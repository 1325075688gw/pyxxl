import typing
from functools import wraps
import json
from django.conf import settings


from django.http import HttpRequest, QueryDict
from marshmallow import ValidationError, EXCLUDE

from peach.misc.exceptions import IllegalRequestException


def validate_parameters(schema: object) -> typing.Callable:
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = args[0]
            if not isinstance(request, HttpRequest):
                raise Exception(
                    "the first parameter must be request, "
                    "you must use @method_decorator(validate_parameters) if you use the class-based View."
                )

            content_type = request.META.get("CONTENT_TYPE")
            if request.method == "GET":
                body = QueryDict(request.META["QUERY_STRING"])
                body = json.loads(body.get("p")) if body.get("p") else body
            else:
                if content_type.startswith("application/json"):
                    body = request.body.decode()
                    body = json.loads(body) if body else dict()
                elif content_type == "application/x-www-form-urlencoded":
                    body = request.body.decode()
                    body = QueryDict(body)
                elif content_type.startswith("multipart/form-data"):
                    body = request.POST
                else:
                    raise IllegalRequestException(
                        "content-type must be application/json or application/x-www-form-urlencoded or multipart/form-data",
                    )
            try:
                request.cleaned_data = schema(unknown=EXCLUDE).load(body)
            except ValidationError as err:
                raise IllegalRequestException(
                    err.messages if settings.DEBUG else "Bad Request"
                )

            return func(*args, **kwargs, cleaned_data=request.cleaned_data)

        return wrapper

    return decorator
