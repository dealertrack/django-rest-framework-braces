from __future__ import absolute_import, print_function, unicode_literals
import inspect

from rest_framework import fields
from rest_framework.fields import *  # noqa
from rest_framework.fields import _UnvalidatedField  # noqa

from .mixins import AllowBlankNullFieldMixin, EmptyStringFieldMixin


FIELDS = [
    'BooleanField',
    'CharField',
    'ChoiceField',
    'DateField',
    'DateTimeField',
    'DecimalField',
    'DurationField',
    'EmailField',
    'FileField',
    'FloatField',
    'HiddenField',
    'ImageField',
    'IntegerField',
    'IPAddressField',
    'MultipleChoiceField',
    'RegexField',
    'SlugField',
    'TimeField',
    'URLField',
    'UUIDField',
]


def get_updated_fields(fields, base_classes):
    fields = [globals()[i] for i in fields]
    return {
        field.__name__: type(field.__name__, base_classes + (field,), {})
        for field in fields
    }


locals().update(
    get_updated_fields(FIELDS, (EmptyStringFieldMixin, AllowBlankNullFieldMixin))
)

__all__ = [name for name, value in locals().items()
           if inspect.isclass(value) and issubclass(value, fields.Field)]
