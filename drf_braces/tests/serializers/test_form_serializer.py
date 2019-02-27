from __future__ import absolute_import, print_function, unicode_literals
import unittest
from collections import OrderedDict
from datetime import datetime

import mock
import six
from django import forms
from rest_framework import fields, serializers

from ...serializers.form_serializer import (
    FormSerializer,
    FormSerializerBase,
    FormSerializerFieldMixin,
    FormSerializerMeta,
    FormSerializerOptions,
    LazyLoadingValidationsMixin,
    make_form_serializer_field,
)


TESTING_MODULE = 'drf_braces.serializers.form_serializer'


class TestForm(forms.Form):
    foo = forms.CharField(max_length=12)
    bar = forms.IntegerField(max_value=500)
    happy = forms.ChoiceField(required=False)
    other = forms.DateTimeField()

    def __init__(self, *args, **kwargs):
        super(TestForm, self).__init__(*args, **kwargs)
        self.fields['happy'].choices = [
            ('happy', 'choices'),
        ]

    def clean(self):
        data = super(TestForm, self).clean()
        data.update({
            'bar': 257,
        })
        return data


class CaptureFailedFieldValidationFieldMixin(FormSerializerFieldMixin):

    def capture_failed_field(self, field_name, field_data, error_msg):
        self._failed_validation = {field_name: (field_data, error_msg)}


class TestFormSerializerFieldMixin(unittest.TestCase):
    def setUp(self):
        super(TestFormSerializerFieldMixin, self).setUp()

        class Field(FormSerializerFieldMixin, fields.IntegerField):
            pass

        class CaptureFailedField(CaptureFailedFieldValidationFieldMixin, fields.TimeField):
            pass

        class Serializer(serializers.Serializer):
            field = Field()
            field_two = CaptureFailedField()

            class Meta(object):
                minimum_required = []
                failure_mode = 'fail'

        self.serializer = Serializer()
        self.field = self.serializer.fields['field']

    def test_run_validation_invalid(self):
        with self.assertRaises(fields.ValidationError):
            self.field.run_validation('a')

    def test_run_validation_invalid_failure_mode(self):
        self.serializer.partial = True

        with self.assertRaises(fields.ValidationError):
            self.field.run_validation('a')

    def test_run_validation_invalid_required_field(self):
        self.serializer.partial = True
        self.serializer.Meta.failure_mode = 'drop'
        self.serializer.Meta.minimum_required = ['field']

        with self.assertRaises(fields.ValidationError):
            self.field.run_validation('a')

    def test_run_validation_skip(self):
        self.serializer.partial = True
        self.serializer.Meta.failure_mode = 'drop'
        self.serializer.Meta.minimum_required = []

        with self.assertRaises(fields.SkipField):
            self.field.run_validation('a')

    def test_run_validation_skip_capture(self):
        self.serializer.partial = True
        self.serializer.Meta.failure_mode = 'drop'
        self.serializer.Meta.minimum_required = []
        self.field_two = self.serializer.fields['field_two']

        with self.assertRaises(fields.SkipField):
            self.field_two.run_validation('Really Bad Time')

        self.assertEqual('Really Bad Time', self.field_two._failed_validation['field_two'][0])
        self.assertIn('Time has wrong format. Use one of these formats instead', six.text_type(self.field_two._failed_validation['field_two'][1]))


class TestUtils(unittest.TestCase):
    def test_make_form_serializer_field(self):
        field_class = make_form_serializer_field(fields.IntegerField)

        self.assertEqual(field_class.__name__, 'IntegerFormSerializerField')
        self.assertTrue(issubclass(field_class, FormSerializerFieldMixin))


class TestFormSerializerOptions(unittest.TestCase):
    def test_init(self):
        meta = mock.Mock(failure_mode='fail', foo='bar')

        options = FormSerializerOptions(meta, 'foo')

        self.assertEqual(options.form, meta.form)
        self.assertEqual(options.failure_mode, 'fail')
        self.assertEqual(options.minimum_required, meta.minimum_required)
        self.assertEqual(options.field_mapping, meta.field_mapping)
        self.assertEqual(options.foo, meta.foo)

    def test_init_invalid(self):
        with self.assertRaises(AssertionError):
            FormSerializerOptions(mock.Mock(failure_mode='foo'), 'foo')
        with self.assertRaises(AssertionError):
            FormSerializerOptions(mock.Mock(form=None), 'foo')
        with self.assertRaises(NotImplementedError):
            FormSerializerOptions(mock.Mock(failure_mode='ignore'), 'foo')


class TestFormSerializerMeta(unittest.TestCase):
    @mock.patch(TESTING_MODULE + '.FormSerializerOptions')
    def test_no_parents(self, mock_form_serializer_options):
        class TestSerializer(six.with_metaclass(FormSerializerMeta, serializers.Serializer)):
            pass

        self.assertFalse(mock_form_serializer_options.called)

    def test_no_meta(self):
        with self.assertRaises(AssertionError):
            class TestSerializer(six.with_metaclass(FormSerializerMeta, FormSerializer)):
                pass

    def test_new(self):
        class TestSerializer(six.with_metaclass(FormSerializerMeta, FormSerializer)):
            class Meta(object):
                form = TestForm

        self.assertIsInstance(TestSerializer.Meta, FormSerializerOptions)
        self.assertIs(TestSerializer.Meta.form, TestForm)


class TestFormSerializerBase(unittest.TestCase):
    def setUp(self):
        super(TestFormSerializerBase, self).setUp()

        class Serializer(FormSerializerBase):
            other = fields.CharField()

            class Meta(object):
                failure_mode = 'drop'
                form = TestForm
                minimum_required = ['foo']
                field_mapping = {}

            def capture_failed_fields(self, raw_data, form_errors):
                self._failed_validation = {k: v for k, v in raw_data.items() if k in form_errors}

        self.serializer_class = Serializer

    def test_init(self):
        serializer = self.serializer_class()

        self.assertTrue(serializer.partial)

    def test_get_form(self):
        serializer = self.serializer_class()

        form = serializer.get_form()

        self.assertIsInstance(form, TestForm)
        self.assertIn('foo', form.fields)
        self.assertIn('bar', form.fields)
        self.assertIn('other', form.fields)
        self.assertTrue(form.fields['foo'].required)
        self.assertFalse(form.fields['bar'].required)
        self.assertFalse(form.fields['other'].required)

    def test_get_fields(self):
        serializer = self.serializer_class()
        serializer.Meta.field_mapping.update({
            forms.CharField: fields.BooleanField,
        })

        serializer_fields = serializer.get_fields()

        self.assertIsInstance(serializer_fields, OrderedDict)
        self.assertIn('foo', serializer_fields)
        self.assertIn('bar', serializer_fields)
        self.assertIn('other', serializer_fields)
        self.assertIsInstance(serializer_fields['foo'], fields.BooleanField)
        self.assertIsInstance(serializer_fields['bar'], fields.IntegerField)
        self.assertIsInstance(serializer_fields['other'], fields.CharField)

    def test_get_fields_excluded(self):
        serializer = self.serializer_class()
        serializer.Meta.exclude = ['foo']
        serializer.Meta.field_mapping.update({
            forms.CharField: fields.BooleanField,
        })

        serializer_fields = serializer.get_fields()

        self.assertIsInstance(serializer_fields, OrderedDict)
        self.assertNotIn('foo', serializer_fields)

    def test_get_fields_not_mapped(self):
        serializer = self.serializer_class()

        class FooField(forms.Field):
            pass

        class FooForm(TestForm):
            stuff = FooField()

        serializer.Meta.form = FooForm

        with self.assertRaises(TypeError):
            serializer.get_fields()

    def test_get_field(self):
        serializer = self.serializer_class()
        form_field = forms.ChoiceField(
            choices=[('foo', 'bar')],
            required=False,
            validators=[mock.sentinel.validator],
        )

        field = serializer._get_field(form_field, fields.ChoiceField)

        self.assertIsInstance(field, fields.ChoiceField)
        self.assertTrue(field.allow_blank)
        self.assertTrue(field.allow_null)
        self.assertListEqual(field.validators, [mock.sentinel.validator])
        self.assertDictEqual(field.choice_strings_to_values, {
            'foo': 'foo',
        })

    def test_get_field_kwargs(self):
        serializer = self.serializer_class()
        form_field = forms.IntegerField(
            max_value=500,
            initial=100,
            required=True,
            validators=[mock.sentinel.validator],
        )

        kwargs = serializer._get_field_kwargs(form_field, fields.IntegerField)

        self.assertDictContainsSubset({
            'default': 100,
            'validators': [mock.sentinel.validator, mock.ANY],
        }, kwargs)
        self.assertNotIn('required', kwargs)

    def test_get_field_kwargs_choice_field(self):
        serializer = self.serializer_class()
        form_field = forms.ChoiceField(
            choices=[('foo', 'FOO'), ('bar', 'BAR')]
        )

        kwargs = serializer._get_field_kwargs(form_field, fields.ChoiceField)

        self.assertDictContainsSubset({
            'choices': OrderedDict([
                ('foo', 'foo'),
                ('bar', 'bar'),
            ]),
        }, kwargs)

    def test_validate(self):
        serializer = self.serializer_class(data={
            'foo': 'hello',
            'bar': '100',
            'other': 'stuff',
        })

        self.assertTrue(serializer.is_valid())
        self.assertDictEqual(serializer.validated_data, {
            'foo': 'hello',
            'bar': 257,
            'happy': '',
        })

    def test_validate_valid(self):
        serializer = self.serializer_class(data={
            'foo': 'hello',
            'bar': '100',
            'other': '2015-01-01 12:30',
        })

        self.assertTrue(serializer.is_valid())
        self.assertDictEqual(serializer.validated_data, {
            'other': datetime(2015, 1, 1, 12, 30),
            'foo': 'hello',
            'bar': 257,
            'happy': '',
        })

    def test_validate_fail(self):
        self.serializer_class.Meta.failure_mode = 'fail'
        serializer = self.serializer_class(data={
            'foo': 'hello',
            'bar': '100',
            'other': 'stuff',
        })

        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(serializer.errors, {
            'other': ['Enter a valid date/time.'],
        })

    def test_validate_capture_errors(self):
        self.serializer_class.Meta.failure_mode = 'drop'
        serializer = self.serializer_class(data={
            'foo': 'Chime Oduzo',
            'bar': 45,
            'other': 'Extremely bad time'
        })
        self.assertTrue(serializer.is_valid())
        self.assertDictEqual(serializer.validated_data, {
            'foo': 'Chime Oduzo',
            'bar': 257,
            'happy': '',
        })
        self.assertDictEqual({'other': 'Extremely bad time'}, serializer._failed_validation)

    def test_to_representation(self):
        with self.assertRaises(NotImplementedError):
            self.serializer_class().to_representation({})


class TestFormSerializer(unittest.TestCase):
    def test_bases(self):
        self.assertTrue(issubclass(FormSerializer, FormSerializerBase))
        self.assertIsInstance(FormSerializer, FormSerializerMeta)


class TestLazyLoadingValidationsMixin(unittest.TestCase):
    def setUp(self):
        super(TestLazyLoadingValidationsMixin, self).setUp()

        class Serializer(LazyLoadingValidationsMixin, FormSerializer):
            class Meta(object):
                form = TestForm

        self.serializer_class = Serializer

    def test_repopulate_form_fields(self):
        serializer = self.serializer_class()

        # sanity check
        self.assertDictEqual(serializer.fields['happy'].choices, {})

        serializer.repopulate_form_fields()

        self.assertDictEqual(dict(serializer.fields['happy'].choices), {'happy': 'happy'})
        self.assertDictEqual(dict(serializer.fields['happy'].choice_strings_to_values),
                             {'happy': 'happy'})

    @mock.patch.object(serializers.Serializer, 'to_internal_value')
    @mock.patch.object(LazyLoadingValidationsMixin, 'repopulate_form_fields')
    def test_to_internal_value(self, mock_repopulate_form_fields, mock_super_to_internal_value):
        serializer = self.serializer_class()

        serializer.to_internal_value({})

        mock_repopulate_form_fields.assert_called_once_with()
