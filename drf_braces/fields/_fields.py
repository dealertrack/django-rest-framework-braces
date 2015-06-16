from __future__ import print_function, unicode_literals
import inspect

from rest_framework import fields
from rest_framework.fields import *  # noqa
from rest_framework.fields import _UnvalidatedField  # noqa

from .mixins import AllowBlankFieldMixin, EmptyStringFieldMixin


EMPTY_STRING_FIELDS = [
    fields.DecimalField,
    fields.IntegerField,
    fields.DateTimeField,
    fields.DateField,
    fields.TimeField,
]

ALLOW_BLANK_FIELDS = [
    fields.CharField,
    fields.RegexField,
]


def get_updated_fields(fields, base_class):
    return {
        field.__name__: type(field.__name__, (base_class, field), {})
        for field in fields
    }


locals().update(get_updated_fields(EMPTY_STRING_FIELDS, EmptyStringFieldMixin))
locals().update(get_updated_fields(ALLOW_BLANK_FIELDS, AllowBlankFieldMixin))

__all__ = [name for name, value in locals().items()
           if inspect.isclass(value) and issubclass(value, fields.Field)]
