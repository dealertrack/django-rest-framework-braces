from __future__ import absolute_import, print_function, unicode_literals
import json
from collections import OrderedDict

import six
from django.conf import settings
from rest_framework import parsers


class SortedJSONParser(parsers.JSONParser):
    """
    Parses JSON-serialized data into OrderedDict.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            return json.loads(data, object_pairs_hook=OrderedDict)
        except ValueError as exc:
            raise parsers.ParseError('JSON parse error - %s' % six.text_type(exc))


# TODO Create a Renderer that does the opposite of this parser.
class StrippingJSONParser(parsers.JSONParser):
    """
    Strip the outer layer of JSON, returning only inner layer.

    This is a convenience class, so that API creators do not need
    to wrap their serializers in a "parent serializer" for the sole
    purpose of stripping out the top-level node.

    Place desired root into parser-context as 'parse-root'.
    Only supports descending one level of nesting.

    Caller is expected to add 'parse_root' to the parser's
    context; a convenient place to do this is in a GenericApiView
    subclass's `get_parser_context()` method.

    Example, for parse_root of "dt_application"::

        input json:
            {
                "dt_application": {
                    "node1": 1234
                }
            }
        output dictionary:
            {
                "node1": 1234
            }
    """

    def parse(self, stream, media_type=None, parser_context=None):
        data = super(StrippingJSONParser, self).parse(
            stream, media_type=media_type, parser_context=parser_context
        )

        try:
            root = parser_context.pop('parse_root')
        except KeyError:
            pass
        else:
            if root in data:
                return data[root]

        return data
