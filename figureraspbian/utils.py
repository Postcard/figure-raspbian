# -*- coding: utf8 -*-

from os.path import basename
import urllib
from urlparse import urlsplit
import random


def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.unquote(urlsplit(url)[2]))


def weighted_choice(choices):
    """ Weighted random.choice """
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w
    assert False, "Shouldn't get here"