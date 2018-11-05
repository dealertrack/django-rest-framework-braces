from __future__ import absolute_import, print_function, unicode_literals
import unittest

from ...fields import _fields
from ...fields.mixins import AllowBlankNullFieldMixin, EmptyStringFieldMixin


class TestFields(unittest.TestCase):
    def test_subclasses(self):
        for f in _fields.FIELDS:
            f = getattr(_fields, f)
            self.assertTrue(issubclass(f, EmptyStringFieldMixin))
            self.assertTrue(issubclass(f, AllowBlankNullFieldMixin))
