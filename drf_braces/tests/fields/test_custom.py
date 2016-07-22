from __future__ import print_function, unicode_literals
import unittest
from collections import OrderedDict

import mock
import pytz

from drf_braces.fields.custom import (
    NonValidatingChoiceField,
    PositiveIntegerField,
    UTCDateTimeField,
    UnvalidatedField,
)


class TestUnvalidatedField(unittest.TestCase):
    def test_run_validators(self):
        validator = mock.MagicMock()
        field = UnvalidatedField(validators=[validator])

        actual = field.run_validators(mock.sentinel.value)

        self.assertIsNone(actual)
        self.assertFalse(validator.called)


class TestPositiveIntegerField(unittest.TestCase):
    def test_init_default(self):
        field = PositiveIntegerField()
        self.assertEqual(field.min_value, 0)

    def test_init_passed(self):
        field = PositiveIntegerField(min_value=mock.sentinel.min_value)
        self.assertEqual(field.min_value, mock.sentinel.min_value)


class TestUTCDateTimeField(unittest.TestCase):
    def test_init(self):
        field = UTCDateTimeField()

        self.assertEqual(
            getattr(field, 'timezone', getattr(field, 'default_timezone', None)),
            pytz.UTC
        )


class TestNonValidatingChoiceField(unittest.TestCase):
    def test_init(self):
        field = NonValidatingChoiceField()

        self.assertEqual(field.choices, OrderedDict())

    def test_to_internal_value(self):
        field = NonValidatingChoiceField(choices=['bar'])

        self.assertEqual(field.to_internal_value('bar'), 'bar')
        self.assertEqual(field.to_internal_value('haha'), 'haha')
