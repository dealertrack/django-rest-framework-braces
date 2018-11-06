from __future__ import absolute_import, print_function, unicode_literals
import unittest

import mock
from rest_framework import fields

from ...fields.mixins import (
    AllowBlankNullFieldMixin,
    EmptyStringFieldMixin,
    ValueAsTextFieldMixin,
)


class TestEmptyStringFieldMixin(unittest.TestCase):
    def setUp(self):
        super(TestEmptyStringFieldMixin, self).setUp()

        class Field(EmptyStringFieldMixin, fields.IntegerField):
            pass

        self.field = Field()

    def test_validate_empty_values_empty_string_required(self):
        with self.assertRaises(fields.ValidationError):
            self.field.validate_empty_values('')

    def test_validate_empty_values_empty_string(self):
        self.field.required = False

        actual = self.field.validate_empty_values('')

        self.assertTupleEqual(actual, (True, ''))

    def test_validate_empty_values(self):
        self.field.required = False
        self.field.allow_null = True

        actual = self.field.validate_empty_values(None)

        self.assertTupleEqual(actual, (True, None))

    def test_representation(self):
        self.field.required = False

        self.assertEqual(self.field.to_representation('50'), 50)
        self.assertEqual(self.field.to_representation(''), '')

    def test_representation_required(self):
        self.field.required = True

        self.assertEqual(self.field.to_representation('50'), 50)
        with self.assertRaises(ValueError):
            self.field.to_representation('')


class TestAllowBlankFieldMixin(unittest.TestCase):
    def setUp(self):
        super(TestAllowBlankFieldMixin, self).setUp()

        class Field(AllowBlankNullFieldMixin, fields.CharField):
            pass

        self.field_class = Field

    def test_init(self):
        field = self.field_class(required=False)

        self.assertTrue(field.allow_blank)
        self.assertTrue(field.allow_null)


class TestValueAsTextFieldMixin(unittest.TestCase):
    def setUp(self):
        super(TestValueAsTextFieldMixin, self).setUp()

        class Field(ValueAsTextFieldMixin, fields.IntegerField):
            pass

        self.field = Field(required=False, allow_null=True, max_value=100)

    def test_to_string_value(self):
        self.assertIsNone(self.field.to_string_value(None))
        self.assertEqual(self.field.to_string_value(5), '5')

    def test_prepare_value_for_validation(self):
        self.assertEqual(
            self.field.prepare_value_for_validation(mock.sentinel.value),
            mock.sentinel.value
        )

    def test_run_validation(self):
        self.assertIsNone(self.field.run_validation(None))

        self.assertEqual(self.field.run_validation(50), '50')
        with self.assertRaises(fields.ValidationError):
            self.field.run_validation(500)
