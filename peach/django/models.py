import base64
import json
import typing
from enum import Enum
from django.conf import settings


from django.db import models
from django.db.models import ManyToManyField, ForeignKey
from peach.django.json import JsonEncoder

from peach.misc.encrypt import AESCipher


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self, fields=None, exclude=None, return_many_to_many=False):
        """
        返回dict结构对象。
        :param fields: 如果指定fields，则只返回fields里的字段数据
        :param exclude: 如果指定exclude, 则不返回exclude里的字段数据，即使该字段在fields里指定了也不返回
        :param return_many_to_many: 是否返回model里的 ManyToManyField 字段数据, 从性能考虑默认不加载
        :return: dict结构数据
        """
        opts = self._meta
        data = {}
        for f in opts.concrete_fields + opts.many_to_many:
            if fields and f.name not in fields:
                continue
            if exclude and f.name in exclude:
                continue
            if isinstance(f, ManyToManyField):
                if self.pk is None or not return_many_to_many:
                    continue
            if isinstance(f, ForeignKey):
                data[f.name + "_id"] = f.value_from_object(self)
            elif isinstance(f, ManyToManyField):
                data[f.name] = [e.to_dict() for e in f.value_from_object(self)]
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        abstract = True


class ListField(models.CharField):
    """
    自定义ListField，解决如下数据转换问题:
    '1|2|3'  <->  [1, 2, 3]
    """

    def __init__(self, base_type=str, separator="|", *args, **kwargs):
        self.separator = separator
        self.base_type = base_type
        super().__init__(*args, **kwargs)

    def get_db_prep_save(self, value, connection):
        if not value:
            return None
        assert isinstance(value, list)
        for v in value:
            assert isinstance(v, self.base_type)
        return self.get_prep_value(value)

    def to_python(self, value):
        if self.base_type in {str, int}:
            if not value:
                return None
            return [self.base_type(v) for v in value.split(self.separator) if v]
        elif self.base_type == dict:
            if not value:
                return []
            return json.loads(value)

    def get_prep_value(self, value):
        if self.base_type in {str, int}:
            return (
                self.separator
                + self.separator.join(str(v) for v in value)
                + self.separator
            )
        elif self.base_type == dict:
            return json.dumps(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)


_AES = AESCipher(base64.b64decode(settings.DB_AES_KEY))


class EncryptField(models.CharField):
    """
    数据脱敏字段
    """

    def __init__(self, base_type=models.CharField, *args, **kwargs):
        assert issubclass(base_type, models.CharField)
        self.base_type = base_type
        super().__init__(*args, **kwargs)

    def get_db_prep_save(self, value: str, connection):
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        if value:
            value = base64.b64encode(_AES.encrypt(value.encode())).decode()
        return value

    def to_python(self, value: str):
        if value:
            value = _AES.decrypt(base64.b64decode(value)).decode()
        return value

    def from_db_value(self, value: str, expression, connection):
        return self.to_python(value)


class DictField(models.CharField):
    """
    自定义DictField，解决如下数据转换问题:
    能支持json.dumps和json.loads处理的数据结构。
    """

    def get_db_prep_save(self, value, connection):
        if not value:
            return None
        assert isinstance(value, dict)
        return json.dumps(value, cls=JsonEncoder)

    def to_python(self, value):
        if not value:
            return dict()
        return json.loads(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)


class EnumMix:
    def __init__(self, base_type: typing.Type[Enum] = None, *args, **kwargs):
        self.base_type = base_type
        super().__init__(*args, **kwargs)  # type: ignore

    def get_db_prep_save(self, value: Enum, connection):
        if value is None:
            return None
        assert isinstance(value, Enum)
        return value.value

    def get_prep_value(self, value: Enum):
        return value.value

    def to_python(self, value: str):
        if value is None:
            return None
        return self.base_type(value)

    def from_db_value(self, value: str, expression, connection):
        return self.to_python(value)


class EnumField(EnumMix, models.CharField):
    pass


class IntEnumField(EnumMix, models.SmallIntegerField):
    pass


def paginate(query, page_no, page_size):
    return query[((page_no - 1) * page_size) : page_no * page_size]
