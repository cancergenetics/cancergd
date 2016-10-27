#!/usr/bin/env python

# This will remove everything from the cache.

import os

# PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) # Full path to my django project directory, which is: "/home/cgenetics/cancergd/"

PROJECT = 'cgdd'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", PROJECT+".settings")

# Needs the following django.setup(), otherwise get exception about: django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
import django
django.setup()
from django.conf import settings
from django.core.cache import cache

print(cache.clear())
print("Cleared cache\n")
