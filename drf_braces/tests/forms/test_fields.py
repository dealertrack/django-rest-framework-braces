from __future__ import absolute_import, print_function, unicode_literals
import unittest
from datetime import datetime

import pytz
from dateutil.tz import tzoffset
from django import forms
from rest_framework import ISO_8601

from ...forms.fields import ISO8601DateTimeField


class TestISO8601DateTimeField(unittest.TestCase):
    def test_to_python_empty(self):
        field = ISO8601DateTimeField(required=False)

        self.assertIsNone(field.clean(''))

    def test_to_python_not_iso8601(self):
        field = ISO8601DateTimeField()

        self.assertEqual(field.clean('2015-01-01 16:30'), datetime(2015, 1, 1, 16, 30))
        with self.assertRaises(forms.ValidationError):
            field.clean('2015-01-01T16:30')

    def test_to_python_iso8601(self):
        field = ISO8601DateTimeField(input_formats=[ISO_8601])

        self.assertEqual(
            field.clean('2015-01-01 16:30'),
            datetime(2015, 1, 1, 16, 30)
        )
        self.assertEqual(
            field.clean('2015-01-01T16:30'),
            datetime(2015, 1, 1, 16, 30)
        )
        self.assertEqual(
            field.clean('2015-01-01T16:30+00:00'),
            datetime(2015, 1, 1, 16, 30).replace(tzinfo=pytz.UTC)
        )
        self.assertEqual(
            field.clean('2015-01-01T16:30+04:00'),
            datetime(2015, 1, 1, 16, 30).replace(tzinfo=tzoffset(None, 4 * 60 * 60))
        )
        with self.assertRaises(forms.ValidationError):
            field.clean('2015-01-01T16:30+A')
