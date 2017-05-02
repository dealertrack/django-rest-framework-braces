from __future__ import absolute_import, print_function, unicode_literals
import inspect

import six
from django import forms
from django.forms.forms import DeclarativeFieldsMetaclass
from rest_framework import serializers

from .. import fields
from ..utils import (
    initialize_class_using_reference_object,
    reduce_attr_dict_from_base_classes,
)
from .fields import ISO8601DateTimeField


SERIALIZER_FORM_FIELD_MAPPING = {
    fields.BooleanField: forms.BooleanField,
    fields.CharField: forms.CharField,
    fields.ChoiceField: forms.ChoiceField,
    fields.DateTimeField: ISO8601DateTimeField,
    fields.EmailField: forms.EmailField,
    fields.IntegerField: forms.IntegerField,
    fields.UUIDField: forms.UUIDField,
    fields.URLField: forms.URLField,
    fields.DateField: forms.DateField,
    serializers.BooleanField: forms.BooleanField,
    serializers.CharField: forms.CharField,
    serializers.ChoiceField: forms.ChoiceField,
    serializers.DateTimeField: ISO8601DateTimeField,
    serializers.EmailField: forms.EmailField,
    serializers.IntegerField: forms.IntegerField,
    serializers.UUIDField: forms.UUIDField,
    serializers.URLField: forms.URLField,
    serializers.DateField: forms.DateField,
}


class SerializerFormOptions(object):
    def __init__(self, options=None, name=None):
        self.serializer = getattr(options, 'serializer', None)
        self.fields = getattr(options, 'fields', [])
        self.exclude = getattr(options, 'exclude', [])
        self.field_mapping = getattr(options, 'field_mapping', {})

        assert self.serializer is not None, (
            '{}.Meta.serializer must be provided'
            ''.format(name)
        )
        assert issubclass(self.serializer, serializers.BaseSerializer), (
            '{}.Meta.serializer must be a subclass of DRF serializer'
            ''.format(name)
        )


class SerializerFormMeta(DeclarativeFieldsMetaclass):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, SerializerForm)]
        except NameError:
            # We are defining SerializerForm itself
            parents = None

        meta = attrs.pop('Meta', None)

        if not parents or attrs.pop('_is_base', False):
            return super(SerializerFormMeta, cls).__new__(cls, name, bases, attrs)

        attrs['_meta'] = options = SerializerFormOptions(meta, name=name)

        new_attrs = cls.get_form_fields_from_serializer(bases, options)
        # attrs should take priority in case a specific field is overwritten
        new_attrs.update(attrs)

        return super(SerializerFormMeta, cls).__new__(cls, name, bases, new_attrs)

    @classmethod
    def get_field_mapping(cls, bases, options):
        mapping = reduce_attr_dict_from_base_classes(
            bases,
            lambda i: getattr(getattr(i, '_meta', None), 'field_mapping', {}),
            SERIALIZER_FORM_FIELD_MAPPING
        )
        mapping.update(options.field_mapping)
        return mapping

    @classmethod
    def get_form_fields_from_serializer(cls, bases, options):
        fields = {}

        mapping = cls.get_field_mapping(bases, options)

        for name, field in options.serializer._declared_fields.items():
            if field.read_only:
                continue

            if name not in options.fields or name in options.exclude:
                continue

            form_field_class = mapping.get(type(field))

            if not form_field_class:
                raise TypeError(
                    '{} is not mapped to appropriate form field class. '
                    'Please add it to the mapping via `field_mapping` '
                    'Meta attribute.'
                    ''.format(type(field))
                )

            fields[name] = initialize_class_using_reference_object(field, form_field_class)

        return fields


class SerializerFormBase(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SerializerFormBase, self).__init__(*args, **kwargs)
        # instantiated during validation
        self.serializer = None

    def get_serializer_context(self):
        return {}

    def get_serializer_data(self):
        data = self.initial.copy()
        data.update(self.cleaned_data or {})
        return data

    def get_serializer(self):
        return self._meta.serializer(
            data=self.get_serializer_data(),
            context=self.get_serializer_context()
        )

    def _clean_form(self):
        super(SerializerFormBase, self)._clean_form()

        self.serializer = self.get_serializer()

        if not self.serializer.is_valid():
            self._errors.update(self.serializer.errors)
        else:
            self.cleaned_data.update(self.serializer.validated_data)


class SerializerForm(six.with_metaclass(SerializerFormMeta, SerializerFormBase)):
    _is_base = True


def form_from_serializer(serializer, **kwargs):
    assert inspect.isclass(serializer) and issubclass(serializer, serializers.BaseSerializer), (
        'Can only create forms from DRF Serializers'
    )
    kwargs.update({'serializer': serializer})
    meta = type(str('Meta'), (object,), kwargs)
    return type(str('{}Form'.format(serializer.__name__)), (SerializerForm,), {'Meta': meta})
