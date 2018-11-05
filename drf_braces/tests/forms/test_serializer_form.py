from __future__ import absolute_import, print_function, unicode_literals
import unittest
from datetime import datetime

import mock
import six
from django import forms
from rest_framework import serializers

from ...forms.serializer_form import (
    SERIALIZER_FORM_FIELD_MAPPING,
    SerializerForm,
    SerializerFormBase,
    SerializerFormMeta,
    SerializerFormOptions,
    form_from_serializer,
)


TESTING_MODULE = 'drf_braces.forms.serializer_form'


class TestSerializer(serializers.Serializer):
    foo = serializers.CharField(read_only=True)
    bar = serializers.IntegerField(min_value=0)
    exclude = serializers.DateTimeField()

    def validate_bar(self, value):
        if value >= 1000:
            raise serializers.ValidationError('Serializer failure')
        return value


class TestForm(SerializerForm):
    class Meta(object):
        serializer = TestSerializer
        fields = ['bar', 'foo']
        exclude = ['exclude']


class TestSerializerFormOptions(unittest.TestCase):
    def test_init(self):
        _options = mock.Mock(serializer=serializers.Serializer)

        options = SerializerFormOptions(_options)

        self.assertEqual(options.serializer, _options.serializer)
        self.assertEqual(options.fields, _options.fields)
        self.assertEqual(options.exclude, _options.exclude)
        self.assertEqual(options.field_mapping, _options.field_mapping)

    def test_init_no_serializer(self):
        with self.assertRaises(AssertionError):
            SerializerFormOptions(None)

    def test_init_not_drf_serializer(self):
        with self.assertRaises(AssertionError):
            SerializerFormOptions(mock.Mock(serializer=int))


class TestSerializerFormMeta(unittest.TestCase):
    @mock.patch.dict(SERIALIZER_FORM_FIELD_MAPPING, {'base': 'mapping'}, clear=True)
    def test_get_field_mapping(self):
        class Base1B(object):
            class _meta(object):
                field_mapping = {
                    'hello': 'mars',
                    'hi': 'there',
                    'foo': 'bar',
                }

        class Base1A(Base1B):
            class _meta(object):
                field_mapping = {
                    'hello': 'world',
                }

        class Base2(object):
            class _meta(object):
                field_mapping = {
                    'hello': 'sun',
                    'something': 'here',
                }

        class Options(object):
            field_mapping = {
                'foo': 'baar',
                'happy': 'rainbows',
            }

        mapping = SerializerFormMeta.get_field_mapping((Base1A, Base2), Options)

        self.assertDictEqual(mapping, {
            'hi': 'there',
            'hello': 'world',
            'something': 'here',
            'base': 'mapping',
            'foo': 'baar',
            'happy': 'rainbows',
        })

    def test_get_form_fields_from_serializer(self):
        fields = SerializerFormMeta.get_form_fields_from_serializer(
            (object,), mock.Mock(serializer=TestSerializer,
                                 fields=['foo', 'bar'],
                                 exclude=['exclude'],
                                 field_mapping={})
        )

        self.assertSetEqual(set(fields.keys()), {'bar'})
        self.assertIsInstance(fields['bar'], forms.IntegerField)

    def test_get_form_fields_from_serializer_unmapped_field(self):
        class CustomField(serializers.Field):
            pass

        class MySerializer(serializers.Serializer):
            foo = serializers.CharField(read_only=True)
            bar = CustomField()

        with self.assertRaises(TypeError):
            SerializerFormMeta.get_form_fields_from_serializer(
                (object,), mock.Mock(serializer=MySerializer,
                                     fields=['foo', 'bar'],
                                     exclude=[],
                                     field_mapping={})
            )

    @mock.patch(TESTING_MODULE + '.SerializerFormOptions')
    def test_new_no_parents(self, mock_serializer_form_options):
        class TestForm(six.with_metaclass(SerializerFormMeta, forms.Form)):
            pass

        self.assertFalse(mock_serializer_form_options.called)

    def test_new(self):
        class TestForm(six.with_metaclass(SerializerFormMeta, SerializerForm)):
            class Meta(object):
                serializer = TestSerializer
                fields = ['bar', 'foo']
                exclude = ['exclude']

        self.assertIsInstance(TestForm._meta, SerializerFormOptions)
        self.assertSetEqual(set(TestForm.base_fields.keys()), {'bar'})


class TestSerializerFormBase(unittest.TestCase):
    def test_init(self):
        self.assertIsNone(SerializerFormBase().serializer)

    def test_get_serializer_context(self):
        self.assertDictEqual(SerializerFormBase().get_serializer_context(), {})

    def test_get_serializer_data(self):
        form = SerializerFormBase()
        form.cleaned_data = {'hello': 'world'}
        form.initial = {'stuff': 'here', 'hello': 'mars'}

        self.assertDictEqual(form.get_serializer_data(), {
            'hello': 'world',
            'stuff': 'here',
        })

    @mock.patch.object(SerializerFormBase, 'get_serializer_data')
    @mock.patch.object(SerializerFormBase, 'get_serializer_context')
    def test_get_serializer(self, mock_get_serializer_context, mock_get_serializer_data):
        form = SerializerFormBase()
        mock_serializer = mock.Mock()
        form._meta = mock.Mock(serializer=mock_serializer)

        actual = form.get_serializer()

        self.assertEqual(actual, mock_serializer.return_value)
        mock_serializer.assert_called_once_with(
            data=mock_get_serializer_data.return_value,
            context=mock_get_serializer_context.return_value,
        )

    @mock.patch.object(SerializerFormBase, 'get_serializer')
    def test_clean_form_valid(self, mock_get_serializer):
        class TestForm(SerializerFormBase):
            hello = forms.CharField()

        form = TestForm(data={'hello': 'world'})
        mock_get_serializer.return_value.is_valid.return_value = True
        mock_get_serializer.return_value.validated_data = {
            'and': 'mars'
        }

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data, {
            'hello': 'world',
            'and': 'mars',
        })

    @mock.patch.object(SerializerFormBase, 'get_serializer')
    def test_clean_form_invalid(self, mock_get_serializer):
        form = SerializerFormBase(data={})
        mock_get_serializer.return_value.is_valid.return_value = False
        mock_get_serializer.return_value.errors = {
            'field': ['error'],
        }

        self.assertFalse(form.is_valid(), form.errors)

        self.assertEqual(form.errors, {'field': ['error']})


class TestSerializerForm(unittest.TestCase):
    def test_full_clean_valid(self):
        data = {
            'foo': 'anything',
            'bar': '500',
            'exclude': '2015-01-01T12:00'
        }
        initial = {
            'exclude': datetime(2016, 1, 1, 16, 30)
        }

        form = TestForm(data=data, initial=initial)

        self.assertTrue(form.is_valid(), dict(form.errors))
        self.assertDictEqual(form.cleaned_data, {
            'bar': 500,
            'exclude': datetime(2016, 1, 1, 16, 30)
        })

    def test_full_clean_invalid(self):
        data = {
            'foo': 'anything',
            'bar': '1000',
            'exclude': '2015-01-01T12:00'
        }
        initial = {
            'exclude': datetime(2016, 1, 1, 16, 30)
        }

        form = TestForm(data=data, initial=initial)

        self.assertFalse(form.is_valid())
        self.assertIn('bar', form.errors)


class TestUtils(unittest.TestCase):
    def test_form_from_serializer_not_serializer(self):
        with self.assertRaises(AssertionError):
            form_from_serializer(None)

    def test_form_from_serializer(self):
        form = form_from_serializer(TestSerializer, fields=['foo', 'bar'], exclude=['exclude'])

        self.assertTrue(issubclass(form, SerializerForm))
        self.assertIsInstance(form._meta, SerializerFormOptions)
        self.assertListEqual(form._meta.fields, ['foo', 'bar'])
        self.assertListEqual(form._meta.exclude, ['exclude'])
        self.assertIs(form._meta.serializer, TestSerializer)
