from django.urls import path

from .s3_view import S3

urlpatterns = [
    path("fileupload/sign/", S3.as_view()),
]
