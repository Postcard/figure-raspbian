# -*- coding: utf8 -*-

from os.path import basename
import urllib
from urlparse import urlsplit
import random

import requests
from requests.exceptions import Timeout, ConnectionError

from . import settings


def internet_on():
    """
    Check if our device has access to the internet
    """
    try:
        requests.get(settings.PING_ADDRESS, timeout=1)
        return True
    except Timeout:
        pass
    except ConnectionError:
        pass
    return False


def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.unquote(urlsplit(url)[2]))
