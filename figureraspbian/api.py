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
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
})


def get_installation():
    url = "%s/resiniodevices/%s/" % (settings.API_HOST, settings.RESIN_DEVICE_UUID)
    r = session.get(url=url, timeout=6)
    if r.status_code == 200:
        return json.loads(r.text)['active_installation']
    else:
        raise ApiException("Failed retrieving installation")


def get_scenario(scenario_id):
    url = "%s/scenarios/%s/?fields=name,ticket_template" % (settings.API_HOST, scenario_id)
    r = session.get(url=url, timeout=3)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        raise ApiException("Failed retrieving scenario")


def download(url, path):
    """
    Download a file from a remote url and copy it to the local path
    """
    local_name = url2name(url)
    req = urllib2.Request(url)
    try:
        r = urllib2.urlopen(req)
        if r.url != url:
            # if we were redirected, the real file name we take from the final URL
            local_name = url2name(r.url)
        path_to_file = join(path, local_name)
        with open(path_to_file, 'wb+') as f:
            f.write(r.read())
        return path_to_file
    except urllib2.HTTPError as e:
        raise ApiException('Failed downloading resource %s with error %s' % (url, e.msg))


def create_random_text_selection(variable, value):
    url = "%s/randomtextselections/" % settings.API_HOST
    data = {
        'variable': variable,
        'value': value
    }
    r = session.post(url, data=data, timeout=10)
    if r.status_code == 201:
        return json.loads(r.text)['id']
    else:
        raise ApiException("Failed creating ticket with message %s" % r.text)


def create_random_image_selection(variable, value):
    url = "%s/randomimageselections/" % settings.API_HOST
    data = {
        'variable': variable,
        'value': value
    }
    r = session.post(url, data=data, timeout=10)
    if r.status_code == 201:
        return json.loads(r.text)['id']
    else:
        raise ApiException("Failed creating ticket with message %s" % r.text)


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
        'rdm_text_selections': serialize(ticket['random_text_selections']),
        'rdm_image_selections': serialize(ticket['random_image_selections']),
        'installation': ticket['installation']
    }
    r = session.post(url, files=files, data=data, timeout=15)
    if r.status_code == 201:
        return json.loads(r.text)['id']
    else:
        raise ApiException("Failed creating ticket with message %s" % r.text)







