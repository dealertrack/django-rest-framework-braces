from __future__ import print_function, unicode_literals

import six
from rest_framework.fields import empty


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
