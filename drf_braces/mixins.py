from __future__ import absolute_import, print_function, unicode_literals

from .parsers import StrippingJSONParser


class MultipleSerializersViewMixin(object):
    def get_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop('serializer_class', None)
        if serializer_class is None:
            serializer_class = self.get_serializer_class()

        kwargs['context'] = self.get_serializer_context()

        return serializer_class(*args, **kwargs)


class MapDataViewMixin(object):
    # Configuration for data mapper.
    # Leave None if you don't require mapping
    data_mapper_class = None

    def get_mapper_context(self):
        return self.get_serializer_context()

    def get_data(self, mapper_class=None):
        """
        Get data for serialization.
        """
        if not mapper_class:
            mapper_class = self.data_mapper_class

        if mapper_class is not None:
            return mapper_class(context=self.get_mapper_context())(self.request.data)

        return self.request.data


class StrippingJSONViewMixin(object):
    parser_classes = (StrippingJSONParser,)

    # Location of the root of the data for this api.
    parser_root = None

    def get_parser_context(self, http_request):
        """
        Add 'parser_root' to this view's parser's parse_context.
        Since this view uses a DescendingJSONParser, it uses
        this information to decide what to pull out.
        """
        context = super(StrippingJSONViewMixin, self).get_parser_context(http_request)
        context.update({'parse_root': self.parser_root})
        return context
