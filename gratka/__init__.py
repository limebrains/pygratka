#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

version = '0.0.2'

VERSION = tuple(map(int, version.split('.')))
__version__ = VERSION
__versionstr__ = version

if (2, 7) <= sys.version_info < (3, 7):
    # <https://docs.python.org/2/howto/logging.html#configuring-logging-for-a-library>
    import logging

    logger = logging.getLogger('gratka')
    logger.addHandler(logging.NullHandler())

    if os.getenv('DEBUG'):
        logging.basicConfig(level=logging.INFO)

BASE_URL = 'http://dom.gratka.pl/'

WHITELISTED_DOMAINS = [
    'dom.gratka.pl',
    'www.dom.gratka.pl',
]
