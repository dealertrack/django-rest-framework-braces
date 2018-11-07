# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from rest_framework import serializers

from ...serializers.swapping import SwappingSerializerMixin


class ChildSerializer(serializers.Serializer):
    foo = serializers.IntegerField()
    bar = serializers.CharField()


class ChildAlternativeSerializer(serializers.Serializer):
    foo = serializers.CharField()
    bar = serializers.CharField()


class ParentSerializer(serializers.Serializer):
    child = ChildSerializer()


class GrandParentSerializer(serializers.Serializer):
    parent = ParentSerializer()
    parents = ParentSerializer(many=True)


class TestSwappingSerializerMixin(unittest.TestCase):
    def test_swapping(self):
        class Swappable(SwappingSerializerMixin, GrandParentSerializer):
            class Meta(object):
                swappable_fields = {
                    ChildSerializer: ChildAlternativeSerializer,
                }

        swapped = Swappable()

        self.assertIsInstance(swapped.fields['parent'].fields['child'], ChildAlternativeSerializer)
        self.assertIsInstance(swapped.fields['parents'].child.fields['child'], ChildAlternativeSerializer)
