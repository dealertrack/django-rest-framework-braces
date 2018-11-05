from __future__ import absolute_import, print_function, unicode_literals
import unittest

from rest_framework import fields

from ..utils import (
    find_class_args,
    find_function_args,
    get_attr_from_base_classes,
    get_class_name_with_new_suffix,
)


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

    def test_find_function_args(self):
        def foo(a, b, c):
            pass

        self.assertListEqual(find_function_args(foo), ['a', 'b', 'c'])

    def test_find_function_args_invalid(self):
        self.assertListEqual(find_function_args(None), [])

    def test_find_class_args(self):
        class Bar(object):
            def __init__(self, a, b):
                pass

        class Foo(Bar):
            def __init__(self, c, d):
                super(Foo, self).__init__(None, None)
                pass

        self.assertSetEqual(set(find_class_args(Foo)), {'a', 'b', 'c', 'd'})
