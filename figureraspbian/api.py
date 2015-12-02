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
        'As-User': int(settings.USER),
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json',
})


def get_installation():
    url = "%s/photobooths/%s/" % (settings.API_HOST, settings.RESIN_UUID)
    r = session.get(url=url, timeout=10)
    r.raise_for_status()
    r.encoding = 'utf-8'
    return json.loads(r.text)['active_installation']


def claim_codes():
    url = "%s/codelist/claim/" % (settings.API_HOST)
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


def create_ticket(ticket):

    url = "%s/tickets/" % settings.API_HOST

    try:
        files = {'snapshot': open(ticket['snapshot'], 'rb'), 'ticket': open(ticket['ticket'], 'rb')}
    except Exception as e:
        logger.error(e)
        files = {
            'snapshot': (ticket['filename'], ticket['snapshot']),
            'ticket': (ticket['filename'], ticket['ticket'])
        }

    data = {
        'datetime': ticket['dt'],
        'code': ticket['code'],
        'installation': ticket['installation'],
        'is_door_open': ticket['is_door_open']
    }

    r = session.post(url, files=files, data=data, timeout=20)
    r.raise_for_status()
    r.encoding = 'utf-8'
    return json.loads(r.text)


def set_paper_status(status, printed_paper_length):

    url = "%s/photobooths/%s/" % (settings.API_HOST, settings.RESIN_UUID)

    data = {
        'owner': int(settings.USER),
        'resin_uuid': settings.RESIN_UUID,
        'paper_status': status,
        'printed_paper_length': printed_paper_length
    }

    session.put(url, data=data, timeout=20)




