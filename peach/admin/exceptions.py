from peach.misc.exceptions import BizErrorCode

ERROR_ILLEGAL_PARAMS = BizErrorCode(900, "参数错误")

ERROR_USER_NOT_EXISTS = BizErrorCode(1001, "用户不存在")
ERROR_USER_PASSWORD_INCORRECT = BizErrorCode(1002, "密码不正确")
ERROR_USER_PASSWORD_DIFFERENT = BizErrorCode(1003, "新旧密码不能相同")
ERROR_USER_DISABLED = BizErrorCode(1004, "用户已被禁用")
ERROR_USER_INVALID_TOKEN = BizErrorCode(1005, "未授权用户")
ERROR_USER_NAME_DUPLICATE = BizErrorCode(1006, "用户名已存在")
ERROR_USER_TOKEN_NOT_EXISTS = BizErrorCode(1007, "Token无效")
ERROR_USER_ROLES_NOT_EXISTS = BizErrorCode(1008, "用户尚未分配角色")


ERROR_ROLE_NOT_EXISTS = BizErrorCode(1101, "角色不存在")
ERROR_ROLE_NAME_EXISTS = BizErrorCode(1101, "角色名称重复")
ERROR_ROLE_BIND_ONLY_LEAF_PERMISSION = BizErrorCode(1102, "绑定的权限具有子权限")
ERROR_ROLE_NOT_ALLOW_SET_PERMISSION_ATTR = BizErrorCode(1103, "该权限没有属性可设置")
ERROR_ROLE_CAN_NOT_UPDATE = BizErrorCode(1104, "该角色不允许编辑")
ERROR_ROLE_CAN_NOT_DELETE = BizErrorCode(1105, "该角色当前关联有账号，无法删除")

ERROR_PERMISSION_NOT_EXISTS = BizErrorCode(1201, "权限不存在")
ERROR_PERMISSION_NOT_AUTHORIZED = BizErrorCode(1202, "未授权操作")

ERROR_LIST_FUNC_MISS_ARGS = BizErrorCode(1301, "list function 缺少参数")

ERROR_EXPORT_REPORT_FAILED = BizErrorCode(2000, "报表导出失败")

ERROR_VCODE_EMPTY = BizErrorCode(3215, "验证码为空")
ERROR_VCODE_INCORRECT = BizErrorCode(3216, "验证码错误")
