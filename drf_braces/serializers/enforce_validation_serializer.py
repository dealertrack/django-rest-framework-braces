from __future__ import absolute_import, print_function, unicode_literals
import inspect

from rest_framework import fields, serializers
from rest_framework.fields import empty

from ..utils import add_base_class_to_instance, get_class_name_with_new_suffix


class EnforceValidationFieldMixin(object):
    """
    Custom DRF field mixin which allows to ignore validation error
    if the field is not mandatory.

    The field is mandatory when the parent serializer includes it
    in the ``must_validate_fields`` list or ``must_validate_fields``
    list is completely omitted. If the list is omitted, then all
    fields in that serializer are mandatory and must validate.
    """

    def run_validation(self, data=empty):
        try:
            return super(EnforceValidationFieldMixin, self).run_validation(data)
        except serializers.ValidationError as e:
            must_validate_fields = getattr(self.parent, 'must_validate_fields', None)
            field_name = getattr(self, 'field_name')

            # only re-raise validation error when this field must be validated
            # as defined by must_validate_fields list on the parent serializer
            # or if must_validate_fields is not defined
            if must_validate_fields is None or field_name in must_validate_fields:
                raise
            else:
                self.capture_failed_field(field_name, data, e.detail)
                raise fields.SkipField(
                    'This field "{}" is being skipped as per enforce validation logic.'
                    ''.format(field_name)
                )

    def capture_failed_field(self, field_name, field_data, error_msg):
        """
        Hook for capturing invalid fields. This is used to track which fields have been skipped.

        Args:
            field_name (str): the name of the field whose data failed to validate
            field_data (object): the data of the field that failed validation
            error_msg (str): validation error message

        Returns:
            Not meant to return anything.
        """


def _create_enforce_validation_serializer(serializer, strict_mode_by_default=True, validation_serializer_field_mixin_class=EnforceValidationFieldMixin):
    """
    Recursively creates a copy of a given serializer which enforces ``must_validate_fields``.

    This function recursively copies serializers and replaces all fields
    by adding ``EnforceValidationFieldMixin`` to their mro which then enforces validation
    for fields defined in ``must_validate_fields`` and drops their data for all other fields.

    Args:
        serializer (Serializer): Serializer class or instance to be copied
        strict_mode_by_default (bool): Whether serializer should use strict mode
            when ``must_validate_fields`` is not defined.
            If ``True``, then all fields must be validated by default
            and if ``False``, then all fields can be dropped.
        validation_serializer_field_mixin_class (type): the class used to validate serializer fields

    Returns:
        Recursive copy of the ``serializer`` which will enforce ``must_validate_fields``.
    """
    if inspect.isclass(serializer):
        serializer = type(
            get_class_name_with_new_suffix(
                serializer,
                'Serializer',
                'EnforceValidationSerializer'
            ),
            (serializer,),
            {}
        )
        fields = serializer._declared_fields
        declared_fields = None

    else:
        # when serializer is instance, we still want to create a modified
        # serializer class copy since if we only adjust the fields
        # on the instance, that can complicate introspecting,
        # especially when ``_create_enforce_validation_serializer``
        # is used as decorator
        serializer = add_base_class_to_instance(
            serializer,
            new_name=get_class_name_with_new_suffix(
                serializer.__class__,
                'Serializer',
                'EnforceValidationSerializer'
            )
        )

        if isinstance(serializer, serializers.ListSerializer):
            serializer.child = _create_enforce_validation_serializer(
                serializer.child,
                strict_mode_by_default=strict_mode_by_default,
                validation_serializer_field_mixin_class=validation_serializer_field_mixin_class,
            )

            # kwargs are used to take a deepcopy of the fields
            # so we need to adjust the child kwargs not to loose
            # reference to our custom child serializer
            if 'child' in serializer._kwargs:
                serializer._kwargs['child'] = serializer.child

            return serializer

        fields = serializer.fields
        declared_fields = serializer._declared_fields

    if not strict_mode_by_default and not hasattr(serializer, 'must_validate_fields'):
        serializer.must_validate_fields = []

        # this is necessary for deepcopy to work when
        # root serializer is instantiated it does deepcopy
        # on serializer._declared_fields which re-instantiates
        # all child fields hence must_validate_fields will be lost
        # adding it to the class makes it persistent
        if not inspect.isclass(serializer):
            serializer.__class__.must_validate_fields = []

    # cant use .items() since we need to adjust dictionary
    # within the loop so we cant be looping over the dict
    # at the same time
    # Python 3 even raises exception for this:
    # RuntimeError: dictionary changed size during iteration
    for name in list(fields.keys()):
        field = fields[name]
        replacement = None

        if isinstance(field, serializers.BaseSerializer):
            replacement = _create_enforce_validation_serializer(
                field,
                strict_mode_by_default=strict_mode_by_default,
                validation_serializer_field_mixin_class=validation_serializer_field_mixin_class,
            )

        elif isinstance(field, serializers.Field):
            replacement = add_base_class_to_instance(
                field,
                validation_serializer_field_mixin_class,
                new_name=get_class_name_with_new_suffix(
                    field.__class__,
                    'Field',
                    'EnforceValidationField'
                )
            )

        if replacement is not None:
            if declared_fields is not None:
                declared_fields[name] = replacement

            if replacement.source == name:
                replacement.source = None

            fields[name] = replacement

    return serializer


def create_enforce_validation_serializer(serializer=None, **kwargs):
    """
    Public function that creates a copy of a serializer which enforces ``must_validate_fields``.
    The difference between this function and ``_create_enforce_validation_serializer``
    is that this function can be used both as a direct decorator and decorator with
    parameters.

    For example::

        @create_enforce_validation_serializer
        class MySerializer(BaseSerializer): pass

        # or

        @create_enforce_validation_serializer(param=value)
        class MySerializer(BaseSerializer): pass

        # or

        create_enforce_validation_serializer(
            MySerializer,
            param=value
        )
    """
    # used as direct decorator so then simply return new serializer
    # e.g.  @decorator
    #       class MySerializer(...)
    # or used as regular function
    # e.g. function(Serializer, foo=bar)
    if inspect.isclass(serializer) and issubclass(serializer, serializers.Serializer):
        return _create_enforce_validation_serializer(serializer, **kwargs)

    # used as decorator with parameters
    # e.g.  @decorator(foo=bar)
    #       class MySerializer(...)
    elif serializer is None:
        def inner(serializer):
            return _create_enforce_validation_serializer(serializer, **kwargs)

        return inner

    else:
        raise TypeError(
            'create_enforce_validation_serializer can only be only on serializers. '
            'It was called with "{}"'.format(type(serializer))
        )
