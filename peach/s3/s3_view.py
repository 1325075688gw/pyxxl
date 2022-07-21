from uuid import uuid1

from django.conf import settings
from django.utils.decorators import method_decorator

from peach.misc import dt
from peach.admin.decorators import require_login
from peach.django.decorators import validate_parameters
from peach.django.views import BaseView

from . import s3_form as form
from .services import s3_service


class S3(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(form.S3Schema))
    def get(self, request, cleaned_data):
        path = cleaned_data["path"]
        user_id = request.user_id
        now_time = dt.local_now()
        key = "{}_{}_{}_{}_{}_{}".format(
            path, now_time.year, now_time.month, now_time.day, user_id, uuid1().hex
        )
        return s3_service.generate_pre_url(key, settings.S3_CONF["bucket_name"])
