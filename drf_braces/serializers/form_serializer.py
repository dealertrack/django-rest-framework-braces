from __future__ import absolute_import, print_function, unicode_literals
from collections import OrderedDict

import six
from django import forms
from rest_framework import serializers

from .. import fields
from ..utils import (
    find_matching_class_kwargs,
    get_attr_from_base_classes,
    get_class_name_with_new_suffix,
    reduce_attr_dict_from_instance,
)


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
        except (serializers.ValidationError, forms.ValidationError) as e:
            # Only handle a ValidationError if the full validation is
            # requested or if field is in minimum required in the case
            # of partial validation.
            if any([not self.parent.partial,
                    self.parent.Meta.failure_mode == FormSerializerFailure.fail,
                    self.field_name in self.parent.Meta.minimum_required]):
                raise
            self.capture_failed_field(self.field_name, data, e.detail)
            raise serializers.SkipField

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


def make_form_serializer_field(field_class, validation_form_serializer_field_mixin_class=FormSerializerFieldMixin):
    return type(
        get_class_name_with_new_suffix(field_class, 'Field', 'FormSerializerField'),
        (validation_form_serializer_field_mixin_class, field_class,),
        {}
    )


FORM_SERIALIZER_FIELD_MAPPING = {
    forms.CharField: make_form_serializer_field(fields.CharField),
    forms.MultipleChoiceField: make_form_serializer_field(fields.ChoiceField),
    forms.ChoiceField: make_form_serializer_field(fields.ChoiceField),
    forms.BooleanField: make_form_serializer_field(fields.BooleanField),
    forms.IntegerField: make_form_serializer_field(fields.IntegerField),
    forms.EmailField: make_form_serializer_field(fields.EmailField),
    forms.DateTimeField: make_form_serializer_field(fields.DateTimeField),
    forms.DateField: make_form_serializer_field(fields.DateField),
    forms.TimeField: make_form_serializer_field(fields.TimeField),
}


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
        self.field_mapping = getattr(meta, 'field_mapping', {})
        self.exclude = getattr(meta, 'exclude', [])

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

        # copy all other custom keys
        for k, v in vars(meta).items():
            if hasattr(self, k):
                continue
            setattr(self, k, v)


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


class FormSerializerBase(serializers.Serializer):
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

        super(FormSerializerBase, self).__init__(*args, **kwargs)

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

    def get_fields(self):
        """
        Return all the fields that should be serialized for the form.
        This is a hook provided by parent class.
        :return: dict of {'field_name': serializer_field_instance}
        """
        ret = super(FormSerializerBase, self).get_fields()

        field_mapping = reduce_attr_dict_from_instance(
            self,
            lambda i: getattr(getattr(i, 'Meta', None), 'field_mapping', {}),
            FORM_SERIALIZER_FIELD_MAPPING
        )

        # Iterate over the form fields, creating an
        # instance of serializer field for each.
        form = self.Meta.form
        for field_name, form_field in getattr(form, 'all_base_fields', form.base_fields).items():
            # if field is specified as excluded field
            if field_name in getattr(self.Meta, 'exclude', []):
                continue

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
                    "Please add {field} to {serializer}.Meta.field_mapping. "
                    "Currently mapped fields: {mapped}".format(
                        field=form_field.__class__.__name__,
                        serializer=self.__class__.__name__,
                        mapped=', '.join(sorted([i.__name__ for i in field_mapping.keys()]))
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

        if 'choices' in attrs:
            choices = OrderedDict(attrs['choices']).keys()
            attrs['choices'] = OrderedDict(zip(choices, choices))

        if getattr(form_field, 'initial', None):
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
                self.capture_failed_fields(data, form.errors)
                cleaned_data = {k: v for k, v in data.items() if k not in form.errors}
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

    def capture_failed_fields(self, raw_data, form_errors):
        """
        Hook for capturing all failed form data when the failure mode is not FormSerializerFailure.fail

        Args:
             raw_data (dict): raw form data
             form_errors (dict): all form errors

        Returns:
            Not meant to return anything.
        """


class FormSerializer(six.with_metaclass(FormSerializerMeta, FormSerializerBase)):
    pass


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

        for form_field_name, form_field in getattr(instance, 'all_fields', instance.fields).items():
            if hasattr(form_field, 'choices'):
                # let drf normalize choices down to key: key
                # key:value is unsupported unlike in django form fields
                self.fields[form_field_name].choices = OrderedDict(form_field.choices).keys()
                self.fields[form_field_name].choice_strings_to_values = {
                    six.text_type(key): key for key in OrderedDict(form_field.choices).keys()
                }

    def to_internal_value(self, data):
        """
        We have tons of "choices" loading in form `__init__()`,
        (so that DB query is evaluated at last possible moment) so require the
        use of ``common.common_json.serializers.LazyLoadingValidationsMixin``.
        """
        self.repopulate_form_fields()
        return super(LazyLoadingValidationsMixin, self).to_internal_value(data)


def set_form_partial_validation(form, minimum_required):
    """
    Get a form ready for partial validation.
    For all fields not in `minimum_required`, set
    `Field.required` to False.

    :param minimum_required: list of minimum required fields
    :return: None
    """
    for field_name, field in getattr(form, 'all_fields', form.fields).items():
        if field_name not in minimum_required:
            field.required = False
