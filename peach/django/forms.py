import typing
from abc import abstractmethod
from enum import Enum

from bson import ObjectId
from bson.errors import InvalidId
from django.utils import timezone
from marshmallow import Schema, fields, validates, ValidationError, post_load

from peach.misc.dtos import PaginationCriteriaDTO


class BaseSchema(Schema):
    pass


class PaginationSchema(Schema):
    """
    分页接口参数基类检查器.
    """

    page_no = fields.Integer(missing=1)
    page_size = fields.Integer(missing=30)
    return_total = fields.Boolean(missing=True)
    export = fields.Boolean(missing=False)

    @validates("page_no")
    def validate_page_no(self, value):
        if value < 1:
            raise ValidationError("page_no must great 0")

    @validates("page_size")
    def validate_page_size(self, value):
        if value < 1:
            raise ValidationError("page_size must great 0")
        if value > 1000:
            raise ValidationError("page_size must less 1000")

    @post_load
    def set_page_value(self, data, **kwargs):
        criteria = self.make_criteria(data)
        assert isinstance(criteria, PaginationCriteriaDTO)
        criteria.page_no = data["page_no"]
        criteria.page_size = data["page_size"]
        criteria.export = data["export"]
        criteria.return_total = data["return_total"]
        return criteria

    @abstractmethod
    def make_criteria(self, data):
        pass


class CNDatetimeField(fields.DateTime):
    """
    中国地区常用的 2018-01-01 12:00:00 格式，区别于iso的 2018-01-01T12:00:00
    """

    DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"

    def _deserialize(self, value, attr, data, **kwargs):
        dt = super()._deserialize(value, attr, data, **kwargs)
        if timezone.is_naive(dt) and timezone.get_current_timezone():
            dt = dt.replace(tzinfo=timezone.get_current_timezone())
        return dt


class ListField(fields.Str):
    def __init__(self, cls: type, **kwargs):
        super().__init__(**kwargs)
        self.field_cls = cls

    def _deserialize(self, value, attr, data, **kwargs) -> typing.List:
        s = super()._deserialize(value, attr, data, **kwargs)
        return [self.field_cls(e) for e in s.split(",")]


class LoadDumpOptions(Enum):
    value = 1  # type: ignore
    name = 0  # type: ignore


class LocalDatetimeField(fields.DateTime):
    """
    将local时间转为带时区的utc时间
    """

    DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"

    def _deserialize(self, value, attr, data, **kwargs):
        dt = super()._deserialize(value, attr, data, **kwargs)
        if timezone.is_naive(dt) and timezone.get_current_timezone():
            dt = dt.replace(tzinfo=timezone.get_current_timezone())
        return dt


class EnumField(fields.Field):
    """
    枚举字段
    """

    VALUE = LoadDumpOptions.value
    NAME = LoadDumpOptions.name

    def __init__(
        self, enum, by_value=True, load_by=None, dump_by=None, *args, **kwargs
    ):
        self.enum = enum
        self.by_value = by_value

        if load_by is None:
            load_by = LoadDumpOptions.value if by_value else LoadDumpOptions.name

        if load_by not in LoadDumpOptions:
            raise ValueError(
                "Invalid selection for load_by must be EnumField.VALUE or EnumField.NAME, got {}".format(
                    load_by
                )
            )

        if dump_by is None:
            dump_by = LoadDumpOptions.value if by_value else LoadDumpOptions.name

        if dump_by not in LoadDumpOptions:
            raise ValueError(
                "Invalid selection for load_by must be EnumField.VALUE or EnumField.NAME, got {}".format(
                    dump_by
                )
            )

        self.load_by = load_by
        self.dump_by = dump_by

        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        elif self.dump_by == LoadDumpOptions.value:
            return value.value
        else:
            return value.name

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        elif self.load_by == LoadDumpOptions.value:
            return self._deserialize_by_value(value, attr, data)
        else:
            return self._deserialize_by_name(value, attr, data)

    def _deserialize_by_value(self, value, attr, data):
        try:
            value = self._get_enum_value_type()(value)
            return self.enum(value)
        except ValueError:
            self.fail("by_value", input=value, value=value)

    def _deserialize_by_name(self, value, attr, data):
        if not isinstance(value, str):
            self.fail("must_be_string", input=value, name=value)

        try:
            return getattr(self.enum, value)
        except AttributeError:
            self.fail("by_name", input=value, name=value)

    def _get_enum_value_type(self):
        return type(list(self.enum)[0].value)

    def fail(self, key, **kwargs):
        option_values = ", ".join([str(mem.value) for mem in self.enum])
        option_names = ", ".join([mem.name for mem in self.enum])

        if key == "by_value":
            raise ValidationError(
                "value: <{}> not in [{}]".format(kwargs["value"], option_values)
            )
        elif key == "by_name":
            raise ValidationError(
                "name: <{}> not in [{}]".format(kwargs["name"], option_names)
            )
        else:
            super().fail(key, **kwargs)


class OptionField(fields.Field):
    """
    从预置数据列表中选择一项
    """

    VALUE = LoadDumpOptions.value
    NAME = LoadDumpOptions.name

    def __init__(self, options, *args, **kwargs):
        assert isinstance(options, list)
        assert options, "options must not empty"
        self.options = options
        self.value_type = type(options[0])
        for each in options:
            if self.value_type != type(each):
                assert "each value in options must be same type"

        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            value = self.value_type(value)
            if value not in self.options:
                raise ValidationError(
                    "value: <{}> is not in options: {}".format(value, self.options)
                )
            return value
        except ValueError:
            raise ValidationError(
                "value: <{}> type is not {}".format(value, self.value_type)
            )


class StripStrField(fields.Str):
    def _deserialize(self, value, attr, data, **kwargs):
        stripped_str = super()._deserialize(value, attr, data, **kwargs).strip()
        if self.required and not stripped_str:
            raise self.make_error("前后不能有空格")
        return stripped_str


class ObjectIdField(fields.Str):
    def _deserialize(self, value, attr, data, **kwargs) -> typing.Any:
        value_str = super()._deserialize(value, attr, data, **kwargs)
        try:
            ObjectId(value_str)
        except (TypeError, InvalidId):
            raise ValidationError(
                f"value: {repr(value)} is not a valid 24-character hex string."
            )
        return value_str


class ExportSchema(PaginationSchema):
    """
    导出功能接口
    """

    export = fields.Boolean()

    @post_load
    def post_load_func(self, data):
        if data.get("export"):
            del data["page_no"]
            del data["page_size"]
            if hasattr(data, "order_by"):
                del data["order_by"]
        return data
