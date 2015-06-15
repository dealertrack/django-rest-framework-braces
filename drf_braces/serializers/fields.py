from __future__ import print_function, unicode_literals

from django.core import validators
from django.utils.translation import ugettext_lazy as _
from rest_framework import fields
from rest_framework.fields import *  # noqa


# ##################################################################### #
#                         DRF Replacement Field                         #
# ##################################################################### #


class EmptyStringFieldMixing(object):
    def validate_empty_values(self, data):
        is_empty, data = super(EmptyStringFieldMixing, self).validate_empty_values(data)
        if not is_empty and data == '':
            if self.required:
                self.fail('required')
            else:
                return True, data
        return is_empty, data


class AllowBlankFieldMixin(object):
    def __init__(self, *args, **kwargs):
        if not kwargs.get('required', True):
            kwargs.setdefault('allow_blank', True)
            kwargs.setdefault('allow_null', True)
        super(AllowBlankFieldMixin, self).__init__(*args, **kwargs)


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


locals().update(get_updated_fields(EMPTY_STRING_FIELDS, EmptyStringFieldMixing))
locals().update(get_updated_fields(ALLOW_BLANK_FIELDS, AllowBlankFieldMixin))


# ##################################################################### #
#                          Enhanced DRF Fields                          #
# ##################################################################### #


class BooleanField(fields.BooleanField):
    def __init__(self, *args, **kwargs):
        self.TRUE_VALUES = self.TRUE_VALUES | set(kwargs.pop('true_values', []))
        self.FALSE_VALUES = self.FALSE_VALUES | set(kwargs.pop('false_values', []))
        super(BooleanField, self).__init__(*args, **kwargs)


class DecimalField(fields.DecimalField):
    def __init__(self, max_digits=None, decimal_places=None, *args, **kwargs):
        super(DecimalField, self).__init__(
            max_digits=max_digits, decimal_places=decimal_places,
            *args, **kwargs
        )

    def quantize(self, value):
        if self.max_digits is None:
            return value
        return super(DecimalField, self).quantize(value)


# ##################################################################### #
#                             Custom Fields                             #
# ##################################################################### #


class UnvalidatedField(fields._UnvalidatedField):
    """
    Same as DRF's ``_UnvalidatedField``, except this is a public class.
    """


class PositiveIntegerField(IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('min_value', 0)
        super(PositiveIntegerField, self).__init__(*args, **kwargs)


class NonValidatingChoiceField(EmptyStringFieldMixing, fields.ChoiceField):
    """
    ChoiceField subclass that skips the validation of "choices".
    It does apply 'required' validation, and any other validation
    done by the parent drf.Field class.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('choices', [])
        super(NonValidatingChoiceField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            return self.choice_strings_to_values[six.text_type(data)]
        except KeyError:
            return six.text_type(data)


class NumericField(EmptyStringFieldMixing, fields.CharField):
    default_error_messages = {
        'invalid': _('Enter a whole number.'),
    }

    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        self.max_value, self.min_value = max_value, min_value
        super(NumericField, self).__init__(*args, **kwargs)

        if max_value is not None:
            self.validators.append(lambda i: validators.MaxValueValidator(max_value)(int(i)))
        if min_value is not None:
            self.validators.append(lambda i: validators.MinValueValidator(min_value)(int(i)))

    def to_internal_value(self, value):
        try:
            value = str(int(value))
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'])
        return value
