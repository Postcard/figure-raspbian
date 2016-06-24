# -*- coding: utf8 -*-

import urllib2
from os.path import join
import logging

import figure

from . import settings
from .utils import url2name

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

figure.api_base = settings.API_HOST
figure.token = settings.TOKEN


def download(url, path):
    """
    Download a file from a remote url and copy it to the local path
    """
    local_name = url2name(url)
    req = urllib2.Request(url)
    r = urllib2.urlopen(req, timeout=10)
    if r.url != url:
        # if we were redirected, the real file name we take from the final URL
        local_name = url2name(r.url)
    path_to_file = join(path, local_name)
    with open(path_to_file, 'wb+') as f:
        f.write(r.read())
    return path_to_file


def create_portrait(portrait):

    try:
        files = {'picture_color': open(portrait['picture'], 'rb'), 'ticket': open(portrait['ticket'], 'rb')}
    except Exception as e:
        logger.error(e)
        files = {
            'picture_color': (portrait['filename'], portrait['picture']),
            'ticket': (portrait['filename'], portrait['ticket'])
        }

    data = {
        'taken': portrait['taken'],
        'place': portrait['place'],
        'event': portrait['event'],
        'photobooth': portrait['photobooth'],
        'code': portrait['code'],
        'is_door_open': portrait['is_door_open']
    }

    figure.Portrait.create(data=data, files=files)

