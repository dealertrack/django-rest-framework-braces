# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import copy

from rest_framework.serializers import BaseSerializer, ListSerializer


class SwappingSerializerMixin(BaseSerializer):
    """
    Declaratively swap any of descendant fields.

    Useful when any of child serializers need to be swapped to similar but slightly different
    serializer. One use case is to swap normal serializer to hyperlinked one...

    For example::

        class SwappedSerializer(SwappingSerializerMixin, MyBaseSerializer):
        class Meta(MyBaseSerializer.Meta):
            swappable_fields = {
                MySerializer: MyOtherSerializer,
            }

    .. note::
        ``MyOtherSerializer`` will be instantiated with same ``*args, **kwargs`` as given to ``MySerializer``.
        This allows to swap fields but to leave state as is.
    """
    def __init__(self, *args, **kwargs):
        super(SwappingSerializerMixin, self).__init__(*args, **kwargs)
        self.swap_fields(self)

    def swap_fields(self, serializer):
        for name, field in list(serializer.fields.items()):
            new_field = self.swap_field(field)
            if new_field is not field:
                serializer.fields[name] = new_field
            if isinstance(new_field, ListSerializer):
                self.swap_fields(new_field.child)
            elif isinstance(new_field, BaseSerializer):
                self.swap_fields(new_field)
        return serializer

    def swap_field(self, field):
        replacement = getattr(self.Meta, "swappable_fields", {}).get(field.__class__)
        if replacement is None:
            return field

        field_copy = copy.deepcopy(field)
        return replacement(*field_copy._args, **field_copy._kwargs)
