from __future__ import absolute_import, print_function, unicode_literals
import unittest

import mock
from rest_framework.generics import GenericAPIView

from ..mixins import (
    MapDataViewMixin,
    MultipleSerializersViewMixin,
    StrippingJSONViewMixin,
)


class TestMultipleSerializersViewMixin(unittest.TestCase):
    def setUp(self):
        super(TestMultipleSerializersViewMixin, self).setUp()

        class View(MultipleSerializersViewMixin, GenericAPIView):
            pass

        self.view = View()

    @mock.patch.object(GenericAPIView, 'get_serializer_context')
    @mock.patch.object(GenericAPIView, 'get_serializer_class')
    def test_get_serializer(self,
                            mock_get_serializer_class,
                            mock_get_serializer_context):
        context = {'context': 'here'}
        mock_get_serializer_context.return_value = context

        serializer = self.view.get_serializer(hello='world')

        self.assertEqual(serializer, mock_get_serializer_class.return_value.return_value)
        mock_get_serializer_class.assert_called_once_with()
        mock_get_serializer_class.return_value.assert_called_once_with(
            hello='world', context=context
        )
        mock_get_serializer_context.assert_called_once_with()

    @mock.patch.object(GenericAPIView, 'get_serializer_context')
    @mock.patch.object(GenericAPIView, 'get_serializer_class')
    def test_get_serializer_with_class(self,
                                       mock_get_serializer_class,
                                       mock_get_serializer_context):
        context = {'context': 'here'}
        mock_get_serializer_context.return_value = context
        serializer_class = mock.MagicMock()

        serializer = self.view.get_serializer(hello='world', serializer_class=serializer_class)

        self.assertEqual(serializer, serializer_class.return_value)
        self.assertFalse(mock_get_serializer_class.called)
        serializer_class.assert_called_once_with(hello='world', context=context)
        mock_get_serializer_context.assert_called_once_with()


class TestMapDataViewMixin(unittest.TestCase):
    def setUp(self):
        super(TestMapDataViewMixin, self).setUp()

        class View(MapDataViewMixin, GenericAPIView):
            pass

        self.view = View()
        self.view.request = mock.MagicMock(data=mock.sentinel.data)

    def test_get_data_no_mapper(self):
        actual = self.view.get_data()

        self.assertEqual(actual, mock.sentinel.data)

    @mock.patch.object(GenericAPIView, 'get_serializer_context')
    def test_get_data_attribute_mapper(self, mock_get_serializer_context):
        mapper = self.view.data_mapper_class = mock.MagicMock()
        actual = self.view.get_data()

        self.assertEqual(actual, mapper.return_value.return_value)
        mapper.assert_called_once_with(
            context=mock_get_serializer_context.return_value
        )
        mapper.return_value.assert_called_once_with(mock.sentinel.data)

    @mock.patch.object(GenericAPIView, 'get_serializer_context')
    def test_get_data_provided(self, mock_get_serializer_context):
        mapper = mock.MagicMock()
        actual = self.view.get_data(mapper_class=mapper)

        self.assertEqual(actual, mapper.return_value.return_value)
        mapper.assert_called_once_with(
            context=mock_get_serializer_context.return_value
        )
        mapper.return_value.assert_called_once_with(mock.sentinel.data)


class TestStrippingJSONViewMixin(unittest.TestCase):
    def setUp(self):
        super(TestStrippingJSONViewMixin, self).setUp()

        class View(StrippingJSONViewMixin, GenericAPIView):
            pass

        self.view = View()
        self.view.request = mock.MagicMock()

    def test_get_parser_context(self):
        self.view.parser_root = mock.sentinel.parser_root

        actual = self.view.get_parser_context(self.view.request)

        self.assertIn('parse_root', actual)
        self.assertEqual(actual['parse_root'], mock.sentinel.parser_root)
