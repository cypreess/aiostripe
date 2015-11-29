import logging
import os
from io import StringIO as sio


class StringIO:
    StringIO = sio


from urllib.parse import parse_qsl

logger = logging.getLogger('stripe')

__all__ = ['StringIO', 'parse_qsl', 'json', 'utf8']

try:
    import json
except ImportError:
    json = None


def utf8(value):
    return value


def is_appengine_dev():
    return ('APPENGINE_RUNTIME' in os.environ and
            'Dev' in os.environ.get('SERVER_SOFTWARE', ''))
