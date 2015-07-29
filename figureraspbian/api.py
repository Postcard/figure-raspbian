# -*- coding: utf8 -*-

import json
import urllib2
from os.path import join

import requests

from . import settings
from .utils import url2name


class ApiException(Exception):
    """Something went wrong while querying the API"""
    pass


session = requests.Session()
session.headers.update({
        'As-User': int(settings.USER),
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json',
})


def get_installation():
    url = "%s/photobooths/%s/" % (settings.API_HOST, settings.RESIN_UUID)
    r = session.get(url=url, timeout=10)
    if r.status_code == 200:
        r.encoding = 'utf-8'
        return json.loads(r.text)['active_installation']
    elif r.status_code == 404:
        return None
    else:
        raise ApiException("Failed retrieving installation")


def get_codes(installation):
    url = "%s/installations/%s/codes/" % (settings.API_HOST, installation)
    r = session.get(url=url, timeout=20)
    if r.status_code == 200:
        r.encoding = 'utf-8'
        return json.loads(r.text)['codes']
    else:
        raise ApiException('Fail retrieving codes')


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
    files = {'snapshot': open(ticket['snapshot'], 'rb'), 'ticket': open(ticket['ticket'], 'rb')}

    # serialize random selections to be posted as a multipart/form-data
    def serialize(selections):
        serialized = ','.join(['%s:%s' % (selection[0], selection[1]['id']) for selection in selections])
        return serialized

    data = {
        'datetime': ticket['dt'],
        'code': ticket['code'],
        'random_text_selections': serialize(ticket['random_text_selections']),
        'random_image_selections': serialize(ticket['random_image_selections']),
        'installation': ticket['installation']
    }

    r = session.post(url, files=files, data=data, timeout=20)
    if r.status_code == 201:
        r.encoding = 'utf-8'
        return json.loads(r.text)
    else:
        raise ApiException("Failed creating ticket with message %s" % r.text)


def set_paper_status(status):

    url = "%s/photobooths/%s/" % (settings.API_HOST, settings.RESIN_UUID)

    data = {
        'owner': int(settings.USER),
        'resin_uuid': settings.RESIN_UUID,
        'paper_status': status
    }

    session.put(url, data=data, timeout=20)






