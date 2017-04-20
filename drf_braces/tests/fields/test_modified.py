from __future__ import print_function, unicode_literals
import unittest
from decimal import Decimal

import pytz
from django.test.utils import override_settings

from drf_braces.fields.modified import BooleanField, CurrencyField, DateTimeField, DecimalField


class TestBooleanField(unittest.TestCase):
    def test_init(self):
        field = BooleanField(true_values=['Y', 'Yes'], false_values=['N', 'No'])
        self.assertIn('Y', field.TRUE_VALUES)
        self.assertIn('Yes', field.TRUE_VALUES)
        self.assertIn('N', field.FALSE_VALUES)
        self.assertIn('No', field.FALSE_VALUES)


class TestDecimalField(unittest.TestCase):
    def test_init(self):
        field = DecimalField()
        self.assertIsNone(field.max_digits)
        self.assertIsNone(field.decimal_places)

    def test_quantize(self):
        field = DecimalField()
        self.assertIsNone(field.quantize(None))

        field = DecimalField(max_digits=4, decimal_places=3)
        self.assertEqual(field.quantize(Decimal('5.1234567')), Decimal('5.123'))


class TestCurrencyField(unittest.TestCase):
    def test_init(self):
        field = CurrencyField()
        self.assertIsNone(field.max_digits)

    def test_to_internal_value(self):
        field = CurrencyField()
        self.assertEqual(field.to_internal_value(5.2345), 5.23)
        self.assertEqual(field.to_internal_value(5.2356), 5.24)
        self.assertEqual(field.to_internal_value(4.2399), 4.24)


class TestDateTimeField(unittest.TestCase):
    @override_settings(USE_TZ=True)
    def test_init(self):
        value = '2015-01-02T16:00'

        self.assertIsNotNone(DateTimeField(default_timezone=pytz.utc).run_validation(value).tzinfo)
        self.assertIsNone(DateTimeField(default_timezone=None).run_validation(value).tzinfo)
