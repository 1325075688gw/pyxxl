from dataclasses import asdict

from django.utils.decorators import method_decorator

from .const import DEFAULT_PASSWORD
from .decorators import (
    require_login,
    check_permission,
    check_user_vcode,
    require_vcode,
)
from .dto import UserListCriteria, RoleListCriteria, RecordListCriteria
from .forms import (
    RegisterSchema,
    LoginSchema,
    UpdateUserPasswordSchema,
    GetUserSchema,
    AddUserSchema,
    UpdateUserSchema,
    GetRoleSchema,
    AddRoleSchema,
    UpdateRoleSchema,
    RecordListSchema,
)
from .helper import wrapper_record_info
from .services import admin_service
from peach.django.decorators import validate_parameters
from peach.django.views import BaseView, PaginationResponse
from peach.report import ReportClient
from peach.report.api import report_client

#######################################
#######################################
# 当前登录用户操作
# 用户注册，登录，登出, 重置密码


class RegisterView(BaseView):
    @method_decorator(validate_parameters(RegisterSchema))
    def post(self, request, cleaned_data):
        user = admin_service.add_user(**cleaned_data, enable=True)
        return user


class LoginView(BaseView):
    @method_decorator(validate_parameters(LoginSchema))
    def post(self, request, cleaned_data):
        user = admin_service.login(**cleaned_data)
        check_user_vcode(request, user["id"])
        admin_service.update_user_login_count(user["id"])
        admin_service.update_user_last_login_time(user["id"])
        return user


class LogoutView(BaseView):
    @method_decorator(require_login)
    def post(self, request):
        user = request.user
        admin_service.logout(user["id"], request.token)


class UserInfoView(BaseView):
    @method_decorator(require_login)
    def get(self, request):
        user = admin_service.get_user_by_id(request.user_id, with_roles=True)
        user["permissions"] = list(
            admin_service.get_user_all_permission_codes(request.user_id)
        )
        return user


class UserUpdatePasswordView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(require_vcode)
    @method_decorator(validate_parameters(UpdateUserPasswordSchema))
    def put(self, request, cleaned_data):
        admin_service.reset_password_after_verify_old_success(
            request.user_id, **cleaned_data
        )
        return dict(id=request.user_id)


class UserResetPasswordView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(require_vcode)
    @method_decorator(check_permission("reset_user_password"))
    def put(self, request, user_id):
        admin_service.reset_password(user_id, DEFAULT_PASSWORD)
        return dict(password=DEFAULT_PASSWORD)


#######################################
#######################################
# 用户管理
class UserListView(BaseView):
    @method_decorator(require_login)
    # @method_decorator(check_permission("admin_user_get"))
    @method_decorator(validate_parameters(GetUserSchema))
    def get(self, request, cleaned_data: UserListCriteria):
        pagination_dto = admin_service.list_users(cleaned_data)
        return PaginationResponse(pagination_dto.total, pagination_dto.data)

    @method_decorator(require_login)
    @method_decorator(require_vcode)
    @method_decorator(check_permission("admin_user_add"))
    @method_decorator(validate_parameters(AddUserSchema))
    def post(self, request, cleaned_data):
        user = admin_service.add_user(**cleaned_data)
        return user


class UserDetailView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("admin_user_get"))
    def get(self, request, user_id):
        user = admin_service.get_user_by_id(
            user_id, check_enable=False, with_roles=True
        )
        return user

    @method_decorator(require_login)
    @method_decorator(require_vcode)
    @method_decorator(check_permission("admin_user_update"))
    @method_decorator(validate_parameters(UpdateUserSchema))
    def put(self, request, user_id, cleaned_data):
        admin_service.update_user(user_id, **cleaned_data)
        return dict(id=user_id)

    @method_decorator(require_login)
    @method_decorator(require_vcode)
    @method_decorator(check_permission("admin_user_delete"))
    def delete(self, request, user_id):
        admin_service.delete_user(user_id)
        return dict(id=user_id)


class UserEnableView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("admin_user_enable"))
    def put(self, request, user_id):
        admin_service.enable_user(user_id)
        return dict(id=user_id)


class UserDisableView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("admin_user_disable"))
    def put(self, request, user_id):
        admin_service.disable_user(user_id)
        return dict(id=user_id)


#######################################
#######################################
# 角色管理
class RoleListView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("admin_role_get"))
    @method_decorator(validate_parameters(GetRoleSchema))
    def get(self, request, cleaned_data: RoleListCriteria):
        pagination_dto = admin_service.list_roles(cleaned_data)
        return PaginationResponse(pagination_dto.total, pagination_dto.data)

    @method_decorator(require_login)
    @method_decorator(require_vcode)
    @method_decorator(check_permission("admin_role_add"))
    @method_decorator(validate_parameters(AddRoleSchema))
    def post(self, request, cleaned_data):
        role = admin_service.add_role(**cleaned_data)
        return role


class RoleDetailView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("admin_role_get"))
    def get(self, request, role_id):
        role = admin_service.get_role(role_id=role_id, with_permissions=True)
        return role

    @method_decorator(require_login)
    @method_decorator(require_vcode)
    @method_decorator(check_permission("admin_role_update"))
    @method_decorator(validate_parameters(UpdateRoleSchema))
    def put(self, request, role_id, cleaned_data):
        admin_service.update_role(role_id, **cleaned_data)
        return dict(id=role_id)

    @method_decorator(require_login)
    @method_decorator(check_permission("admin_role_delete"))
    def delete(self, request, role_id):
        admin_service.delete_role(role_id)
        return dict(id=role_id)


class RoleAllView(BaseView):
    @method_decorator(require_login)
    def get(self, request):
        role = admin_service.get_all_roles()
        return role


#######################################
#######################################
# 权限管理


class PermissionListView(BaseView):
    @method_decorator(require_login)
    def get(self, request):
        tree = admin_service.get_total_permission_tree()
        return dict(permissions=tree)


class ResourceOptionView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("record_get"))
    def get(self, request):
        resource_map = admin_service.get_resource_map()
        return [e for e in resource_map]


#######################################
#######################################
# 操作记录管理


class RecordListView(BaseView):
    @method_decorator(require_login)
    @method_decorator(check_permission("record_get"))
    @method_decorator(validate_parameters(RecordListSchema))
    def get(self, request, cleaned_data: RecordListCriteria):
        if cleaned_data.export:
            return self.export(request, cleaned_data)
        total, records = admin_service.get_record_list(cleaned_data)
        records = wrapper_record_info(records)
        return PaginationResponse(total, records)

    @method_decorator(check_permission("record_export"))
    def export(self, request, cleaned_data: RecordListCriteria):
        res = report_client.add_report_task(
            report_type="admin_record",
            file_type=ReportClient.FileType.XLSX,
            user_id=request.user_id,
            filter_params=asdict(cleaned_data),
        )
        return dict(task_id=res["id"])
