import json
import requests
from . import settings
from selenium import webdriver


def create_ticket(snapshot):
    url = "%s/tickets/" % settings.API_HOST
    files = {'snapshot': open(snapshot, 'rb')}
    data = {'scenario': settings.SCENARIO}
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.post(url, files=files, data=data, headers=headers, timeout=15)
    if r.status_code == 201:
        return json.loads(r.text)['id']
    else:
        raise Exception("Failed creating ticket with message %s" % r.text)


def get_installation():
    url = "%s/installations/%s" % (settings.API_HOST, settings.INSTALLATION)
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.get(url=url, headers=headers, timeout=3)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return Exception("Failed retrieving installation")


def get_scenario(scenario_id):
    url = "%s/scenarios/%s" % (settings.API_HOST, scenario_id)
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.get(url=url, headers=headers, timeout=3)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return Exception("Failed retrieving scenario")




phantomjs = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH, service_args=['--ignore-ssl-errors=true'])

# TODO find a way to protect resource but still be able to use PhantomJS

def render_ticket(id):
    url = "%s/tickets/%s/render/" % (settings.API_HOST, id)
    phantomjs.get(url)
    phantomjs.save_screenshot(settings.TICKET)
    return settings.TICKET







