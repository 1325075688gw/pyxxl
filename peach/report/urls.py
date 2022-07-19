from django.urls import path

from .views import ReportDogTaskView, ReportDogTaskDetailView

urlpatterns = [
    path("report_client_task/", ReportDogTaskView.as_view()),
    path("report_client_task/<int:task_id>/", ReportDogTaskDetailView.as_view()),
]
