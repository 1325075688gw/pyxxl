import typing
from dataclasses import dataclass, field

from django.views import View


class BaseView(View):
    SUCCESS_RESPONSE = dict()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response is None:
            return BaseView.SUCCESS_RESPONSE
        return response


@dataclass
class PaginationResponse:
    total: int = 0
    items: typing.List[typing.Any] = field(default_factory=list)
