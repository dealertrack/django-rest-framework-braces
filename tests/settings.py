# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals


DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'drf-braces.sqlite',
    }
}

INSTALLED_APPS = [
    'drf_braces',
    'tests',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_extensions',
]

MIDDLEWARE_CLASSES = []

STATIC_URL = '/static/'
SECRET_KEY = 'foo'

ROOT_URLCONF = 'tests.urls'
