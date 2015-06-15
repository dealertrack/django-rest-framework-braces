from __future__ import print_function, unicode_literals
from collections import OrderedDict

import six
from django import forms
from rest_framework import serializers

from ..utils import (
    find_matching_class_kwargs,
    get_attr_from_base_classes,
    get_class_name_with_new_suffix,
)
from .. import fields


def make_form_serializer_field(field_class):
    return type(
        get_class_name_with_new_suffix(field_class.__class__, 'Field', 'FormSerializerField'),
        (FormSerializerFieldMixin, field_class,),
        {}
    )


FORM_SERIALIZER_FIELD_MAPPING = {
    forms.CharField: make_form_serializer_field(fields.CharField),
    forms.MultipleChoiceField: make_form_serializer_field(fields.ChoiceField),
    forms.ChoiceField: make_form_serializer_field(fields.ChoiceField),
    forms.BooleanField: make_form_serializer_field(fields.BooleanField),
    forms.IntegerField: make_form_serializer_field(fields.IntegerField),
    forms.fields.EmailField: make_form_serializer_field(fields.EmailField),
}


class FormSerializerFailure(object):
    """
    Enum for the possible form validation failure modes.

    'fail': validation failures should be added to self.errors
        and `is_valid()` should return False.

    'drop': validation failures for a given attribute will result in
        that attribute being dropped from `cleaned_data`;
        `is_valid()` will return True.

    'ignore': validation failures will be ignored, and the (invalid)
        data provided will be preserved in `cleaned_data`.
    """
    fail = 'fail'
    drop = 'drop'
    ignore = 'ignore'


class FormSerializerFieldMixin(object):
    def run_validation(self, data):
        try:
            return super(FormSerializerFieldMixin, self).run_validation(data)
        except (serializers.ValidationError, forms.ValidationError):
            # Only handle a ValidationError if the full validation is
            # requested or if field is in minimum required in the case
            # of partial validation.
            if any([not self.parent.partial,
                    self.field_name in self.parent.Meta.minimum_required]):
                raise
            raise serializers.SkipField


class FormSerializerOptions(object):
    """
    Defines what options FormSerializer can have in Meta.

    :param form: The ``django.form.Form`` class to use as the base
        for the serializer.
    :param failure_mode: `FormSerializerFailure`
    :param minimum_required: the minimum required fields that
        must validate in order for validation to succeed.
    """

    def __init__(self, meta, class_name):
        self.form = getattr(meta, 'form', None)
        self.failure_mode = getattr(meta, 'failure_mode', FormSerializerFailure.fail)
        self.minimum_required = getattr(meta, 'minimum_required', [])

        assert self.form, (
            'Class {serializer_class} missing "Meta.form" attribute'.format(
                serializer_class=class_name
            )
        )
        assert self.failure_mode in vars(FormSerializerFailure).values(), (
            'Failure mode "{}" is not supported'.format(self.failure_mode)
        )
        if self.failure_mode == FormSerializerFailure.ignore:
            raise NotImplementedError(
                'Failure mode "{}" is not supported since it is not clear '
                'what is an expected behavior'.format(self.failure_mode)
            )


class FormSerializerMeta(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, FormSerializer)]
        except NameError:
            # We are defining FormSerializer itself
            parents = None

        if not parents or attrs.pop('_is_base', False):
            return super(FormSerializerMeta, cls).__new__(cls, name, bases, attrs)

        assert 'Meta' in attrs, (
            'Class {serializer_class} missing "Meta" attribute'.format(
                serializer_class=name
            )
        )
        options_class = get_attr_from_base_classes(
            bases, attrs, '_options_class', default=FormSerializerOptions
        )
        attrs['Meta'] = options_class(attrs['Meta'], name)

        return super(FormSerializerMeta, cls).__new__(cls, name, bases, attrs)


class FormSerializer(six.with_metaclass(FormSerializerMeta, serializers.Serializer)):
    """
    The base Form serializer class.
    When a subclassing serializer is validated or saved, this will
    pass-through those operations to the mapped Form.
    """
    _is_base = True
    _options_class = FormSerializerOptions

    def __init__(self, *args, **kwargs):
        # We override partial validation handling, since for
        # it to be properly implemented for a Form the caller
        # must also choose whether or not to include the data
        # that failed validation in the result cleaned_data.
        # Unfortunately there is no way to prevent a caller from
        # sending this param themselves, because of the way DRFv2
        # serializers work internally.
        if self.Meta.failure_mode != FormSerializerFailure.fail:
            kwargs['partial'] = True

        self.form_instance = None

        super(FormSerializer, self).__init__(*args, **kwargs)

    def get_form(self, data=None, **kwargs):
        """
        Create an instance of configured form class.

        :param data: optional initial data
        :param kwargs: key args to pass to form instance
        :return: instance of `self.opts.form`, bound if data was provided,
            otherwise unbound.
        """
        form_cls = self.Meta.form

        instance = form_cls(data=data, **kwargs)

        # Handle partial validation on the form side
        if self.partial:
            set_form_partial_validation(
                instance, self.Meta.minimum_required
            )

        return instance

    def _get_field_mapping(self):
        """
        Get the mapping of ``django.forms.fields`` field types to
        ``rest_framework.fields`` types.
        Subclasses can update this mapping by defining a
        `field_mapping` class variable.

        This method does not exist in parent class.

        :return: dict of django field cls --> rest_framework field cls
        """
        field_mapping = {}
        field_mapping.update(self._default_field_mapping)

        # get all field mappings from super methods
        for base in self.__class__.mro()[::-1]:
            field_mapping.update(getattr(base, 'field_mapping', {}))

        # this should of been picked by previous lookup
        # however __init__ can do some magic hence should
        # update just in case
        field_mapping.update(getattr(self, 'field_mapping', {}))

        return field_mapping

    def get_fields(self):
        """
        Return all the fields that should be serialized for the form.
        This is a hook provided by parent class.
        :return: dict of {'field_name': serializer_field_instance}
        """
        ret = super(FormSerializer, self).get_fields()
        form = self.Meta.form
        form_fields = form.base_fields

        field_mapping = self._get_field_mapping()

        # Iterate over the form fields, creating an
        # instance of serializer field for each.
        for field_name, form_field in form_fields.iteritems():
            # if field is already defined via declared fields
            # skip mapping it from forms which then honors
            # the custom validation defined on the DRF declared field
            if field_name in ret:
                continue

            try:
                serializer_field_class = field_mapping[form_field.__class__]
            except KeyError:
                raise TypeError(
                    "{field} is not mapped to a serializer field. "
                    "Please add {field} to {serializer}.Meta.field_mapping".format(
                        field=form_field.__class__.__name__,
                        serializer=self.__class__.__name__,
                    )
                )
            else:
                ret[field_name] = self._get_field(form_field, serializer_field_class)

        return ret

    def _get_field(self, form_field, serializer_field_class):
        kwargs = self._get_field_kwargs(form_field, serializer_field_class)

        field = serializer_field_class(**kwargs)

        for kwarg, value in kwargs.items():
            # set corresponding DRF attributes which don't have alternative
            # in Django form fields
            if kwarg == 'required':
                field.allow_blank = not value
                field.allow_null = not value

            # ChoiceField natively uses choice_strings_to_values
            # in the to_internal_value flow
            elif kwarg == 'choices':
                field.choice_strings_to_values = {
                    six.text_type(key): key for key in OrderedDict(value).keys()
                }

        return field

    def _get_field_kwargs(self, form_field, serializer_field_class):
        """
        For a given Form field, determine what validation attributes
        have been set.  Includes things like max_length, required, etc.
        These will be used to create an instance of ``rest_framework.fields.Field``.

        :param form_field: a ``django.forms.field.Field`` instance
        :return: dictionary of attributes to set
        """
        attrs = find_matching_class_kwargs(form_field, serializer_field_class)

        if hasattr(form_field, 'initial') and form_field.initial:
            attrs['default'] = form_field.initial

        # avoid "May not set both `required` and `default`"
        if attrs.get('required') and 'default' in attrs:
            del attrs['required']

        return attrs

    def validate(self, data):
        """
        Validate a form instance using the data that has been run through
        the serializer field validation.

        :param data: deserialized data to validate
        :return: validated, cleaned form data
        :raise: ``django.core.exceptions.ValidationError`` on failed
            validation.
        """
        self.form_instance = form = self.get_form(data=data)

        if not form.is_valid():
            _cleaned_data = getattr(form, 'cleaned_data', None) or {}

            if self.Meta.failure_mode == FormSerializerFailure.fail:
                raise serializers.ValidationError(form.errors)

            else:
                cleaned_data = data
                # use any cleaned data form might of validated right until
                # this moment even if validation failed
                cleaned_data.update(_cleaned_data)

        else:
            cleaned_data = form.cleaned_data

        return cleaned_data

    def to_representation(self, instance):
        """
        It doesn't make much sense to serialize a Form instance to JSON.
        """
        raise NotImplementedError(
            '{} does not currently serialize Form --> JSON'
            ''.format(self.__class__.__name__)
        )


class LazyLoadingValidationsMixin(object):
    """
    Provides a method for re-evaluating the validations for
    a form using an instance of it (whereas the FormSerializer
    only uses the form class).
    If your form class loads validations in `__init__()`, you
    need this.
    """

    def repopulate_form_fields(self):
        """
        Repopulate the form fields, update choices.
        The repopulation is required b/c some DT forms use a lazy-load approach
        to populating choices of a ChoiceField, by putting the load
        in the form's constructor.  Also, the DT fields may require context_data,
        which is unavailable when the fields are first constructed
        (which happens during evaluation of the serializer classes).
        :return: None
        """
        instance = self.get_form()

        for form_field_name, form_field in instance.fields.iteritems():
            if hasattr(form_field, 'choices'):
                self.fields[form_field_name].choices = form_field.choices
                self.fields[form_field_name].choice_strings_to_values = {
                    six.text_type(key): key for key in OrderedDict(form_field.choices).keys()
                }


class SerializerDataMapper(object):
    """
    Knows how to look at a Serializer and determine how to map
    data to it.
    This class will translate data from dict format A to format B.
    The structure for format B will be inferred from the serializer
    provided in `__init__`.

    :param serializer_class: The serializer that will be destination
    :param serializer_context: The serializer context
    """

    parser_class = None

    def __init__(self, serializer_class, serializer_context):
        self.serializer_class = serializer_class
        self.context = serializer_context

    def map_data(self, data):
        """
        Perform the mapping.
        :param data: input data dictionary
        :return: output data dictionary
        """
        common_json_parser = self.parser_class(context=self.context)
        mapped_data = common_json_parser(data)
        mapped_data = {k: v for k, v in mapped_data.items() if v}

        return mapped_data


def set_form_partial_validation(form, minimum_required):
    """
    Get a form ready for partial validation.
    For all fields not in `minimum_required`, set
    `Field.required` to False.

    :param minimum_required: list of minimum required fields
    :return: None
    """
    for field_name, field in form.fields.iteritems():
        if field_name not in minimum_required:
            field.required = False
