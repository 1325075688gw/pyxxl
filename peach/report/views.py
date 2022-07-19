from django.utils.decorators import method_decorator

from peach.admin.decorators import require_login
from peach.admin.exceptions import ERROR_PERMISSION_NOT_AUTHORIZED
from peach.django.decorators import validate_parameters
from peach.django.views import BaseView
from peach.misc.exceptions import BizException

from .api import report_client
from .forms import TaskListSchema


class ReportDogTaskView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(TaskListSchema))
    def get(self, request, cleaned_data):
        res = report_client.list_tasks(request.user_id, **cleaned_data)
        return res


class ReportDogTaskDetailView(BaseView):
    @method_decorator(require_login)
    def get(self, request, task_id):
        res = report_client.get_download_url(task_id)
        if int(res["user_id"]) != request.user_id:
            raise BizException(ERROR_PERMISSION_NOT_AUTHORIZED)
        return dict(url=res["url"])
