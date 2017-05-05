from __future__ import absolute_import, print_function, unicode_literals

import six
from dateutil.parser import parse
from django import forms
from rest_framework import ISO_8601


class ISO8601DateTimeField(forms.DateTimeField):
    def to_python(self, value):
        if value in self.empty_values:
            return

        if isinstance(value, six.string_types) and ISO_8601 in self.input_formats:
            try:
                return parse(value)
            except ValueError:
                raise forms.ValidationError(self.error_messages['invalid'], code='invalid')

        return super(ISO8601DateTimeField, self).to_python(value)
