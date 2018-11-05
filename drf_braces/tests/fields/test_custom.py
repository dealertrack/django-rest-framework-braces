from __future__ import absolute_import, print_function, unicode_literals
import unittest
from collections import OrderedDict
from decimal import ROUND_DOWN, Decimal

import mock
import pytz

from ...fields.custom import (
    NonValidatingChoiceField,
    PositiveIntegerField,
    RoundedDecimalField,
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


class TestRoundedDecimalField(unittest.TestCase):
    def test_init(self):
        field = RoundedDecimalField()
        self.assertEqual(field.decimal_places, 2)
        self.assertIsNone(field.rounding)

        new_field = RoundedDecimalField(rounding=ROUND_DOWN)
        self.assertEqual(new_field.rounding, ROUND_DOWN)

    def test_to_internal_value(self):
        field = RoundedDecimalField()
        self.assertEqual(field.to_internal_value(5), Decimal('5'))
        self.assertEqual(field.to_internal_value(5.2), Decimal('5.2'))
        self.assertEqual(field.to_internal_value(5.23), Decimal('5.23'))
        self.assertEqual(field.to_internal_value(5.2345), Decimal('5.23'))
        self.assertEqual(field.to_internal_value(5.2356), Decimal('5.24'))
        self.assertEqual(field.to_internal_value('5'), Decimal('5'))
        self.assertEqual(field.to_internal_value('5.2'), Decimal('5.2'))
        self.assertEqual(field.to_internal_value('5.23'), Decimal('5.23'))
        self.assertEqual(field.to_internal_value('5.2345'), Decimal('5.23'))
        self.assertEqual(field.to_internal_value('5.2356'), Decimal('5.24'))
        self.assertEqual(field.to_internal_value(Decimal('5')), Decimal('5'))
        self.assertEqual(field.to_internal_value(Decimal('5.2')), Decimal('5.2'))
        self.assertEqual(field.to_internal_value(Decimal('5.23')), Decimal('5.23'))
        self.assertEqual(field.to_internal_value(Decimal('5.2345')), Decimal('5.23'))
        self.assertEqual(field.to_internal_value(Decimal('5.2356')), Decimal('5.24'))
        self.assertEqual(field.to_internal_value(Decimal('4.2399')), Decimal('4.24'))

        floored_field = RoundedDecimalField(rounding=ROUND_DOWN)
        self.assertEqual(floored_field.to_internal_value(5.2345), Decimal('5.23'))
        self.assertEqual(floored_field.to_internal_value(5.2356), Decimal('5.23'))
        self.assertEqual(floored_field.to_internal_value(Decimal('5.2345')), Decimal('5.23'))
        self.assertEqual(floored_field.to_internal_value(Decimal('5.2356')), Decimal('5.23'))
