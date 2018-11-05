from __future__ import absolute_import, print_function, unicode_literals
import json
import unittest
from collections import OrderedDict

import six
from rest_framework import parsers

from ..parsers import SortedJSONParser, StrippingJSONParser


class TestSortedJSONParser(unittest.TestCase):
    def setUp(self):
        super(TestSortedJSONParser, self).setUp()
        self.parser = SortedJSONParser()

    def test_parser(self):
        content = json.dumps({'hello': 'world'}).encode('utf-8')
        stream = six.BytesIO(content)

        actual_data = self.parser.parse(stream=stream)

        self.assertEqual(actual_data, OrderedDict([('hello', 'world')]))

    def test_parser_invalid_json(self):
        content = (
            json.dumps({'hello': 'world'})
            .replace('"', "'")
            .encode('utf-8')
        )
        stream = six.BytesIO(content)

        with self.assertRaises(parsers.ParseError):
            self.parser.parse(stream=stream)


class TestStrippingJSONParser(unittest.TestCase):
    def setUp(self):
        super(TestStrippingJSONParser, self).setUp()
        self.parser = StrippingJSONParser()

    def test_parser(self):
        content = json.dumps({'root': {'hello': 'world'}}).encode('utf-8')
        stream = six.BytesIO(content)

        actual_data = self.parser.parse(
            stream=stream,
            parser_context={'parse_root': 'root'}
        )

        self.assertEqual(actual_data, OrderedDict([('hello', 'world')]))

    def test_parser_no_root(self):
        content = json.dumps({'root': {'hello': 'world'}}).encode('utf-8')
        stream = six.BytesIO(content)

        actual_data = self.parser.parse(
            stream=stream,
            parser_context={}
        )

        self.assertEqual(actual_data, {'root': {'hello': 'world'}})

    def test_parser_different_root(self):
        content = json.dumps({'root': {'hello': 'world'}}).encode('utf-8')
        stream = six.BytesIO(content)

        actual_data = self.parser.parse(
            stream=stream,
            parser_context={'parse_root': 'foo'}
        )

        self.assertEqual(actual_data, {'root': {'hello': 'world'}})
