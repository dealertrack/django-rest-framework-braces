from __future__ import print_function, unicode_literals

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
        if self.max_digits is None:
            return value
        return super(DecimalField, self).quantize(value)


__all__ = [name for name, value in locals().items() if issubclass(value, fields.Field)]
