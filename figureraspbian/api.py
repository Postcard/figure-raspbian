# -*- coding: utf8 -*-

import json
import urllib2
from os.path import join
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

import requests

from . import settings
from .utils import url2name


session = requests.Session()
session.headers.update({
    'Authorization': 'Bearer %s' % settings.TOKEN,
    'Accept': 'application/json'
})


def get_photobooth():
    url = "%s/photobooths/%s/" % (settings.API_HOST, settings.RESIN_UUID)
    r = session.get(url=url, timeout=10)
    r.raise_for_status()
    r.encoding = 'utf-8'
    return json.loads(r.text)


def claim_codes():
    url = "%s/codelist/claim/" % settings.API_HOST
    r = session.post(url=url, timeout=20)
    r.raise_for_status()
    r.encoding = 'utf-8'
    return json.loads(r.text)['codes']


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

    url = "%s/portraits/" % settings.API_HOST

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
        'code': portrait['code'],
        'is_door_open': portrait['is_door_open']
    }

    r = session.post(url, files=files, data=data, timeout=20)
    r.raise_for_status()
    r.encoding = 'utf-8'
    return json.loads(r.text)


def set_paper_level(paper_level):

    url = "%s/photobooths/%s/" % (settings.API_HOST, settings.RESIN_UUID)

    data = {
        'resin_uuid': settings.RESIN_UUID,
        'paper_level': paper_level
    }

    session.put(url, data=data, timeout=20)




