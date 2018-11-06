from __future__ import absolute_import, print_function, unicode_literals
import unittest
from decimal import Decimal

import pytz
from django.test.utils import override_settings

from ...fields.modified import BooleanField, DateTimeField, DecimalField


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


class TestDateTimeField(unittest.TestCase):
    @override_settings(USE_TZ=True)
    def test_init(self):
        value = '2015-01-02T16:00'

        self.assertIsNotNone(DateTimeField(default_timezone=pytz.utc).run_validation(value).tzinfo)
        self.assertIsNone(DateTimeField(default_timezone=None).run_validation(value).tzinfo)
