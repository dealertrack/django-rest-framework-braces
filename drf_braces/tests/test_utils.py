from __future__ import print_function, unicode_literals

import unittest

from drf_braces.utils import (
    get_class_name_with_new_suffix,
    get_attr_from_base_classes,
)
from rest_framework import fields


class TestUtils(unittest.TestCase):
    def test_get_class_name_with_new_suffix(self):
        new_name = get_class_name_with_new_suffix(
            klass=fields.IntegerField,
            existing_suffix='Field',
            new_suffix='StrawberryFields'
        )
        self.assertEqual(new_name, 'IntegerStrawberryFields')

        new_name = get_class_name_with_new_suffix(
            klass=fields.IntegerField,
            existing_suffix='straws',
            new_suffix='Blueberries'
        )
        self.assertEqual(new_name, 'IntegerFieldBlueberries')

    def test_get_attr_from_base_classes(self):
        Parent = type(str('Parent'), (), {'fields': 'pancakes'})

        self.assertEqual(
            get_attr_from_base_classes((Parent,), [], 'fields'), 'pancakes'
        )

        self.assertEqual(
            get_attr_from_base_classes(
                (Parent,), {'fields': 'mushrooms'}, 'fields'
            ),
            'mushrooms'
        )

        self.assertEqual(
            get_attr_from_base_classes((Parent,), [], '', default='maple_syrup'),
            'maple_syrup'
        )

        with self.assertRaises(AttributeError):
            get_attr_from_base_classes(
                (Parent,), {'fields': 'mushrooms'}, 'catchmeifyoucan'
            )
