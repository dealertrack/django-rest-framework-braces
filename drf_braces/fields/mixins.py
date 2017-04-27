from __future__ import absolute_import, print_function, unicode_literals

import six
from rest_framework.fields import CharField, empty


class EmptyStringFieldMixin(object):
    def validate_empty_values(self, data):
        is_empty, data = super(EmptyStringFieldMixin, self).validate_empty_values(data)
        if not is_empty and data == '':
            if self.required:
                self.fail('required')
            else:
                return True, data
        return is_empty, data

    def to_representation(self, value):
        if value in ('', None) and not self.required:
            return value
        return super(EmptyStringFieldMixin, self).to_representation(value)


class AllowBlankNullFieldMixin(object):
    def __init__(self, *args, **kwargs):
        super(AllowBlankNullFieldMixin, self).__init__(*args, **kwargs)

        # some DRF fields explicitly do not allow some kwargs
        # therefore we adjust the field attributes directly
        if not self.required:
            if all([isinstance(self, CharField),
                    hasattr(self, 'allow_blank'),
                    'allow_blank' not in kwargs]):
                self.allow_blank = True
            if all([hasattr(self, 'allow_null'),
                    'allow_null' not in kwargs]):
                self.allow_null = True


class ValueAsTextFieldMixin(object):
    def to_string_value(self, data):
        if data:
            return six.text_type(data)
        return data

    def prepare_value_for_validation(self, data):
        return data

    def run_validation(self, value=empty):
        (is_empty_value, value) = self.validate_empty_values(value)
        if is_empty_value:
            return value

        value = self.prepare_value_for_validation(value)
        value = self.to_internal_value(value)
        self.run_validators(value)
        value = self.to_string_value(value)

        return value
