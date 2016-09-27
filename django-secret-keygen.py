#!/usr/bin/env python

# Pseudo-random django secret key generator.
# This does print SECRET key to terminal which can be seen as unsafe.
# From: https://gist.github.com/mattseymour/9205591
#   Alternative version: https://gist.github.com/ndarville/3452907

# Can use this script to create secret key file:, eg:
#    django-secret-keygen.py > key.txt

import string
import random

# Get ascii Characters numbers and punctuation (minus quote characters as
# they could terminate string).
chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace(
    '\'', '').replace('"', '').replace('\\', '')

secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(50)])

# or redirect to a file using:  django-secret-keygen.py > cgdd/key.txt
print(secret_key)
