from __future__ import print_function, unicode_literals
import unittest

from drf_braces.fields._fields import (
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    IntegerField,
    RegexField,
    TimeField,
)
from drf_braces.fields.mixins import AllowBlankFieldMixin, EmptyStringFieldMixin


class TestFields(unittest.TestCase):
    def test_subclasses(self):
        fields = [
            DecimalField,
            IntegerField,
            DateTimeField,
            DateField,
            TimeField,
        ]
        for f in fields:
            self.assertTrue(issubclass(f, EmptyStringFieldMixin))

        fields = [
            CharField,
            RegexField,
        ]
        for f in fields:
            self.assertTrue(issubclass(f, AllowBlankFieldMixin))
