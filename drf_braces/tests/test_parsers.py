from __future__ import print_function, unicode_literals
import json
import unittest
from collections import OrderedDict

import six

from drf_braces.parsers import SortedJSONParser


class TestSortedJSONParser(unittest.TestCase):
    def setUp(self):
        super(TestSortedJSONParser, self).setUp()
        self.parser_class = SortedJSONParser()

    def test_sorted_json_parser(self):
        content = json.dumps({"hello": "world"}).encode('utf-8')
        stream = six.BytesIO(content)
        expected_data = OrderedDict([('hello', 'world')])

        actual_data = self.parser_class.parse(stream=stream)

        self.assertEqual(expected_data, actual_data)
