from __future__ import absolute_import, print_function, unicode_literals
import unittest

import mock
import six
from rest_framework import fields, serializers

from ...serializers.enforce_validation_serializer import (
    EnforceValidationFieldMixin,
    _create_enforce_validation_serializer,
    add_base_class_to_instance,
    create_enforce_validation_serializer,
)


TESTING_MODULE = 'drf_braces.serializers.enforce_validation_serializer'


class InnerSerializer(serializers.Serializer):
    field = fields.IntegerField()
    field2 = fields.IntegerField()
    must_validate_fields = ['field']


class TestSerializer(serializers.Serializer):
    field = fields.IntegerField()
    field2 = fields.IntegerField()
    inner = InnerSerializer()


class TestManySerializer(serializers.Serializer):
    many = TestSerializer(many=True)


class CaptureFailedFieldValidationFieldMixin(EnforceValidationFieldMixin):

    def capture_failed_field(self, field_name, field_data, error_msg):
        self._failed_validation = {field_name: (field_data, error_msg)}


class TestEnforceValidationFieldMixin(unittest.TestCase):
    class Field(EnforceValidationFieldMixin, fields.IntegerField):
        pass

    class CaptureFailedField(CaptureFailedFieldValidationFieldMixin, fields.TimeField):
        pass

    def test_run_validation_must_validate(self):
        field = self.Field()
        field.field_name = 'field'
        field.parent = mock.MagicMock(must_validate_fields=None)

        self.assertEqual(field.run_validation('5'), 5)

    def test_run_validation_must_validate_all(self):
        field = self.Field()
        field.field_name = 'field'
        field.parent = mock.MagicMock(must_validate_fields=None)

        with self.assertRaises(serializers.ValidationError):
            field.run_validation('hello')

    def test_run_validation_must_validate_invalid(self):
        field = self.Field()
        field.field_name = 'field'
        field.parent = mock.MagicMock(must_validate_fields=['field'])

        with self.assertRaises(serializers.ValidationError):
            field.run_validation('hello')

    def test_run_validation_must_validate_ignore(self):
        field = self.Field()
        field.field_name = 'field'
        field.parent = mock.MagicMock(must_validate_fields=[])

        with self.assertRaises(serializers.SkipField):
            field.run_validation('hello')

    def test_run_validation_must_validate_ignore_capture(self):
        field = self.CaptureFailedField()
        field.field_name = 'field'
        field.parent = mock.MagicMock(must_validate_fields=[''])

        with self.assertRaises(serializers.SkipField):
            field.run_validation('Bad Time')

        self.assertEqual('Bad Time', field._failed_validation['field'][0])
        self.assertIn('Time has wrong format. Use one of these formats instead', six.text_type(field._failed_validation['field'][1]))


class TestUtils(unittest.TestCase):
    def test_add_base_class_to_instance(self):
        obj = fields.IntegerField(max_value=100)

        self.assertNotIsInstance(obj, EnforceValidationFieldMixin)

        new_obj = add_base_class_to_instance(obj, EnforceValidationFieldMixin)

        self.assertIsInstance(new_obj, EnforceValidationFieldMixin)
        self.assertEqual(vars(obj), vars(new_obj))

    def test__create_enforce_validation_serializer_instance(self):
        new_serializer_class = _create_enforce_validation_serializer(
            TestManySerializer, strict_mode_by_default=False
        )
        new_serializer = new_serializer_class(data={
            'many': [
                {
                    'inner': {
                        'field': '5',
                        'field2': 'hello',
                    },
                    'field': 'hello',
                    'field2': 'world',
                },
            ]
        })

        self.assertIsInstance(
            new_serializer.fields['many'].child.fields['field'],
            EnforceValidationFieldMixin
        )
        self.assertIsInstance(
            new_serializer.fields['many'].child.fields['inner'].fields['field'],
            EnforceValidationFieldMixin
        )
        self.assertListEqual(
            new_serializer.fields['many'].child.must_validate_fields,
            []
        )
        self.assertEqual(
            new_serializer.fields['many'].child.fields['inner'].must_validate_fields,
            ['field']
        )

        self.assertTrue(new_serializer.is_valid(), new_serializer.errors)
        self.assertDictEqual(new_serializer.validated_data, {
            'many': [
                {
                    'inner': {
                        'field': 5,
                    }
                }
            ]
        })

    @mock.patch(TESTING_MODULE + '._create_enforce_validation_serializer')
    def test_create_enforce_validation_serializer_direct_decorator(
            self, mock_create_enforce_validation_serializer):
        @create_enforce_validation_serializer
        class OtherSerializer(TestSerializer):
            pass

        self.assertEqual(OtherSerializer, mock_create_enforce_validation_serializer.return_value)
        mock_create_enforce_validation_serializer.assert_called_once_with(mock.ANY)

    @mock.patch(TESTING_MODULE + '._create_enforce_validation_serializer')
    def test_create_enforce_validation_serializer_decorator_params(
            self, mock_create_enforce_validation_serializer):
        @create_enforce_validation_serializer(foo='bar')
        class OtherSerializer(TestSerializer):
            pass

        self.assertEqual(OtherSerializer, mock_create_enforce_validation_serializer.return_value)
        mock_create_enforce_validation_serializer.assert_called_once_with(mock.ANY, foo='bar')

    def test_create_enforce_validation_serializer_invalid(self):
        with self.assertRaises(TypeError):
            create_enforce_validation_serializer(5)
