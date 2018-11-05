from __future__ import absolute_import, print_function, unicode_literals
import inspect
from decimal import Decimal, getcontext

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


class RoundedDecimalField(fields.DecimalField):
    """
    Currency field subclass of Decimal used for rounding currencies
    to two decimal places.
    """

    def __init__(self, max_digits=None, decimal_places=2, rounding=None, *args, **kwargs):
        super(RoundedDecimalField, self).__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            *args, **kwargs
        )
        self.rounding = rounding

    def to_internal_value(self, data):
        return self.quantize(super(RoundedDecimalField, self).to_internal_value(data))

    def validate_precision(self, data):
        return data

    def quantize(self, data):
        """
        Quantize the decimal value to the configured precision.
        """
        if self.decimal_places is None:
            return data

        context = getcontext().copy()

        if self.max_digits is not None:
            context.prec = self.max_digits
        if self.rounding is not None:
            context.rounding = self.rounding
        return data.quantize(
            Decimal('.1') ** self.decimal_places,
            context=context
        )


__all__ = [name for name, value in locals().items()
           if inspect.isclass(value) and issubclass(value, fields.Field)]
