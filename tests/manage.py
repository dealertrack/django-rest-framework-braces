#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..')))
sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
