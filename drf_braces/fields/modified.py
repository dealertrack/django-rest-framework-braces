from __future__ import absolute_import, print_function, unicode_literals
import inspect

from . import _fields as fields


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
        if self.max_digits is None or self.decimal_places is None:
            return value
        return super(DecimalField, self).quantize(value)


class DateTimeField(fields.DateTimeField):
    def __init__(self, *args, **kwargs):
        super(DateTimeField, self).__init__(*args, **kwargs)
        # allow fo the case when default_timezone is passed as None
        # since super will in that use Django's default timezone
        if 'default_timezone' in kwargs:
            # DRF >= 3.3
            if callable(self.default_timezone):
                self.timezone = kwargs['default_timezone']
            else:
                self.default_timezone = kwargs['default_timezone']


__all__ = [name for name, value in locals().items()
           if inspect.isclass(value) and issubclass(value, fields.Field)]
