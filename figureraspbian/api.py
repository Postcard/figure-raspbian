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
    print url
    r = session.get(url=url, timeout=6)
    print r
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


def download(resource, path):
    """
    Download a file from a remote url and copy it to the local path
    """
    url = "%s/%s" % (settings.API_HOST, resource)
    local_name = url2name(url)
    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    if r.url != url:
        # if we were redirected, the real file name we take from the final URL
        local_name = url2name(r.url)
    path_to_file = join(path, local_name)
    with open(path_to_file, 'wb+') as f:
        f.write(r.read())
    return path_to_file


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


def create_ticket(installation, snapshot, ticket, datetime, code, random_text_selections, random_image_selections):
    url = "%s/tickets/" % settings.API_HOST
    files = {'snapshot': open(snapshot, 'rb'), 'ticket': open(ticket, 'rb')}
    data = {
        'datetime': datetime,
        'code': code,
        'random_text_selections': random_text_selections,
        'random_image_selections': random_image_selections,
        'installation': installation
    }
    r = session.post(url, files=files, data=data, timeout=15)
    if r.status_code == 201:
        return json.loads(r.text)['id']
    else:
        raise ApiException("Failed creating ticket with message %s" % r.text)







