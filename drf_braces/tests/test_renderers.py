# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import datetime
import json
import unittest

from ..renderers import DoubleAsStrJsonEncoder


class TestDoubleAsStrJsonEncoder(unittest.TestCase):
    def test_encode(self):
        self.assertEqual(
            json.loads(json.dumps({
                'a': 12345678901234567890,
                'b': [123],
                'c': datetime.date(2010, 1, 2)
            }, cls=DoubleAsStrJsonEncoder)),
            {
                'a': '12345678901234567890',
                'b': [123],
                'c': '2010-01-02',
            }
        )
