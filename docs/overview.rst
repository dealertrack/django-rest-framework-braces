========
Overview
========

Django-rest-braces (drf-braces) is all about adding useful utilities for working with DRF.
This overview will go over some of the most useful ones. You can refer to the API docs or source
code to see documentation about all of the utilities.

Forms
=====

Many Django applications are built using standard Django practices following basic request-response
data flow. Safe way of dealing with user-input in such applications is to use
Django forms. That works really well until application needs to be extended to introduce services
since many of the forms might need to be rewritten (as serializers when using DRF).
That situation becomes much worse custom forms (not ``ModelForm``) need to be migrated.

Same issue presents itself when Django application is initially started by using services
but later needs to add basic UI using Django forms.

DRF-braces attempts to solve these challenges by providing converters to go from form to
serializer and vise-versa -
:obj:`FormSerializer <drf_braces.serializers.form_serializer.FormSerializer>` and
:obj:`SerializerForm <drf_braces.forms.serializer_form.SerializerForm>`.

FormSerializer
--------------

:obj:`FormSerializer <drf_braces.serializers.form_serializer.FormSerializer>` is a special
serializer class which converts existing ``Form`` to ``Serializer`` while preserving form validation logic.
It works very similar to ``ModelForm`` or ``ModelSerializer``::

    from django import forms
    from drf_braces.serializers.form_serializer import FormSerializer

    class MyForm(forms.Form):
        foo = forms.CharField(max_length=32)
        bar = forms.DateTimeField()

    class MySerializer(FormSerializer):
        class Meta(object):
            form = MyForm

SerializerForm
--------------

:obj:`SerializerForm <drf_braces.forms.serializer_form.SerializerForm>` is a special form class
which converts existing ``Serializer`` to ``Form`` while preserving serializer validation logic.
It works very similar to ``ModelForm`` or ``ModelSerializer``::

    from rest_framework import serializers
    from drf_braces.forms.serializer_form import SerializerForm

    class MySerializer(serializers.Serializer):
        foo = serializers.CharField(max_length=32)
        bar = serializers.DateTimeField()

    class MyForm(SerializerForm):
        class Meta(object):
            serializer = MySerializer

.. warning::
    Currently ``SerializerForm`` does not support nested serializers.

Serializers
===========

Enforce Validation
------------------

DRF has a concept of partial serializers which then only validate data supplied in request payload.
The problem is that if the data is sent, it must be valid and if a single field is invalid,
the whole serializer validation fails and error is returned to the consumer.
That however is not always desired if the application must accept the payload as is
and ignore invalid data.

DRF-braces provides :func:`enforce_validation_serializer <drf_braces.serializers.enforce_validation_serializer>`
which returns a recursive serializer copy does just that. It only enforces validation on specified
fields and if validation fails on non-specified fields, it ignores that data::

    from rest_framework import serializers
    from drf_braces.serializers import enforce_validation_serializer

    class MySerializer(serializers.Serializer):
        must_validate_fields = ['foo']

        foo = serializers.CharField(max_length=32)
        bar = serializers.DateTimeField()

    MyEnforceValidationSerializer = enforce_validation_serializer(MySerializer)

.. note::
    Even though above ``MySerializer`` defines ``must_validate_fields``, ``MySerializer``
    still enforces validation on all fields. Only serializers returned by
    :func:`enforce_validation_serializer <drf_braces.serializers.enforce_validation_serializer>`
    consider ``must_validate_fields`` in field validation.

Mixins
======

* :obj:`MultipleSerializersViewMixin <drf_braces.mixins.MultipleSerializersViewMixin>`
* :obj:`StrippingJSONViewMixin <drf_braces.mixins.StrippingJSONViewMixin>`
* :obj:`MapDataViewMixin <drf_braces.mixins.MapDataViewMixin>`

Parsers
=======

* :obj:`SortedJSONParser <drf_braces.parsers.SortedJSONParser>`
* :obj:`StrippingJSONParser <drf_braces.parsers.StrippingJSONParser>`

Fields
======

Some fields:

* :obj:`UnvalidatedField <drf_braces.fields.custom.UnvalidatedField>`
* :obj:`PositiveIntegerField <drf_braces.fields.custom.PositiveIntegerField>`
* :obj:`NonValidatingChoiceField <drf_braces.fields.custom.NonValidatingChoiceField>`

and mixins:

* :obj:`EmptyStringFieldMixin <drf_braces.fields.mixins.EmptyStringFieldMixin>`
* :obj:`AllowBlankNullFieldMixin <drf_braces.fields.mixins.AllowBlankNullFieldMixin>`
* :obj:`ValueAsTextFieldMixin <drf_braces.fields.mixins.ValueAsTextFieldMixin>`
