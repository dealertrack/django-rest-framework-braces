from __future__ import print_function, unicode_literals
import inspect

import pytz
import six
from django.utils.translation import gettext as _

from . import _fields as fields
from .mixins import ValueAsTextFieldMixin


class UnvalidatedField(fields._UnvalidatedField):
    """
    Same as DRF's ``_UnvalidatedField``, except this is a public class.
    """

    def run_validators(self, value):
        return


class PositiveIntegerField(fields.IntegerField):
    """
    Enhanced DRF's ``IntegerField`` as this default ``min_value`` to be 0
    hence only allowing positive numbers.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('min_value', 0)
        super(PositiveIntegerField, self).__init__(*args, **kwargs)


class UTCDateTimeField(fields.DateTimeField):
    """
    Same as DateTimeField except this field guarantees to return time-zone aware dates.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_timezone', pytz.utc)
        super(UTCDateTimeField, self).__init__(*args, **kwargs)


class NonValidatingChoiceField(fields.ChoiceField):
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


class NumericField(ValueAsTextFieldMixin, fields.IntegerField):
    default_error_messages = {
        'invalid': _('Enter a whole number.'),
    }


__all__ = [name for name, value in locals().items()
           if inspect.isclass(value) and issubclass(value, fields.Field)]


class RoundedDecimalField(fields.DecimalField):
    """
    Currency field subclass of Decimal used for rounding currencies
    to two decimal places.
    """

    def __init__(self, max_digits=100, decimal_places=2, *args, **kwargs):
        super(fields.DecimalField, self).__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            *args, **kwargs
        )

    def quantize(self, data):
        if isinstance(data, float):
            return round(data, self.decimal_places)
        return super(fields.DecimalField, self).quantize(data)

    def to_internal_value(self, data):
        if isinstance(data, float):
            return self.quantize(data)
        return self.quantize(super(RoundedDecimalField, self).to_internal_value(data))

    def validate_precision(self, data):
        return data
