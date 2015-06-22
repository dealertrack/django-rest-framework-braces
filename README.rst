============================
Django Rest Framework Braces
============================

.. image:: https://travis-ci.org/dealertrack/django-rest-braces.svg?branch=master
    :target: https://travis-ci.org/dealertrack/django-rest-braces

.. image:: https://coveralls.io/repos/dealertrack/django-rest-braces/badge.svg
    :target: https://coveralls.io/r/dealertrack/django-rest-braces

Collection of utilities for working with DRF. Name inspired by `django-braces <https://github.com/brack3t/django-braces>`_.

* Free software: MIT license
* GitHub: https://github.com/dealertrack/django-rest-braces
* Documentation: https://django-rest-braces.readthedocs.org.

Installing
----------

Easiest way to install ``django-rest-braces`` is by using ``pip``::

    $ pip install django-rest-braces

Usage
-----

Once installed, you can use any of the supplied utilities by simply importing them.
For example::

    from drf_braces.mixins import MultipleSerializersViewMixin

    class MyViewSet(MultipleSerializersViewMixin, GenericViewSet):
        def create(self, request):
            serializer = self.get_serializer(serializer_class=MySerializer)
            ...

For full list of available utilities, please refer to the `documentation <https://django-rest-braces.readthedocs.org>`_.

Testing
-------

To run the tests you need to install testing requirements first::

    $ make install

Then to run tests, you can use use Makefile command::

    $ make test
