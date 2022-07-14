from django.views import View


class BaseView(View):
    SUCCESS_RESPONSE = dict()

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response is None:
            return BaseView.SUCCESS_RESPONSE
        return response


# @dataclass
# class PaginationResponse:
#     total: int = 0
#     items: typing.List[typing.Any] = field(default_factory=list)


class PaginationResponse:
    def __init__(self, total, items, **kwargs):
        assert total >= 0
        if items:
            assert isinstance(items, list)
        self.total = total
        self.items = items
        self.kwargs = kwargs or dict()
