from __future__ import print_function, unicode_literals


class MultipleSerializersViewMixin(object):
    def get_serializer(self, serializer_class=None, *args, **kwargs):
        if serializer_class is None:
            serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)
