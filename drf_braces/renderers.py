# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from collections import Mapping

import six
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.encoders import JSONEncoder


class DoubleAsStrJsonEncoder(JSONEncoder):
    def _encode(self, o):
        if isinstance(o, Mapping):
            return {k: self._encode(v) for k, v in o.items()}
        elif isinstance(o, (list, tuple)):
            return [self._encode(i) for i in o]
        elif isinstance(o, six.integer_types):
            int_str = six.text_type(o)
            if len(int_str) >= 15:
                o = int_str
        return o

    def encode(self, o):
        return super(DoubleAsStrJsonEncoder, self).encode(self._encode(o))


class DoubleAsStrJsonRenderer(JSONRenderer):
    """
    Regular Json renderer except big integers are converted to strings

    Not all json clients support big integers (e.g. js) hence we need to convert
    all big integers to strings for compatibility reasons.

    For usage, custom ``Accept: application/json; double=str`` needs to be passed.
    """
    encoder_class = DoubleAsStrJsonEncoder
    media_type = 'application/json; double=str'
    format = 'json'
