from django.urls import path
from . import views

urlpatterns = [
    # 注册，登录，登出
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("user_info/", views.UserInfoView.as_view()),
    path("reset_password/", views.UserUpdatePasswordView.as_view()),
    path("reset_password/<int:user_id>/", views.UserResetPasswordView.as_view()),
    # 用户管理
    path("users/", views.UserListView.as_view()),
    path("users/<int:user_id>/", views.UserDetailView.as_view()),
    path("users/<int:user_id>/enable/", views.UserEnableView.as_view()),
    path("users/<int:user_id>/disable/", views.UserDisableView.as_view()),
    # 角色管理
    path("roles/", views.RoleListView.as_view()),
    path("roles/<int:role_id>/", views.RoleDetailView.as_view()),
    path("roles/get_all/", views.RoleAllView.as_view()),
    # 权限管理
    path("permissions/", views.PermissionListView.as_view()),
    # 操作记录
    path("record/", views.RecordListView.as_view()),
    # report_dog
    # path("", include("gis.common.report_dog.urls")),
]
