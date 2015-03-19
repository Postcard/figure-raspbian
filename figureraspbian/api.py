import json
import requests
from . import settings
from selenium import webdriver


def get_data():
    installation = get_installation(settings.INSTALLATION_ID)
    scenario = get_scenario(installation['scenario_obj']['id'])
    ticket_template = scenario['ticket_template']
    text_variables = [get_text_variables(variable_id) for variable_id in ticket_template['text_variables']]
    image_variables = [get_image_variables(variable_id) for variable_id in ticket_template['image_variables']]
    data = {
        'installation': installation,
        'scenario': scenario,
        'ticket_template': ticket_template,
        'text_variables': text_variables,
        'image_variables': image_variables
    }
    return data


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
    url = "%s/scenarios/%s/?fields=name,ticket_template" % (settings.API_HOST, scenario_id)
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.get(url=url, headers=headers, timeout=3)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return Exception("Failed retrieving scenario")


def get_text_variables(variable_id):
    url = "%s/textvariables/%s/" % (settings.API_HOST, variable_id)
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.get(url=url, headers=headers, timeout=3)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return Exception("Failed retrieving textvariable")


def get_image_variables(variable_id):
    url = "%s/textvariables/%s/" % (settings.API_HOST, variable_id)
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.get(url, headers=headers, timeout=3)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return Exception("Failed retrieving imagevariable")


def create_ticket(snapshot, ticket, code, datetime, random_text_selections, random_image_selections):
    url = "%s/tickets/" % settings.API_HOST
    files = {'snapshot': open(snapshot, 'rb'), 'ticket': open(ticket, 'rb')}
    data = {'installation': settings.INSTALLATION_ID, 'code': code, 'datetime': datetime,
            'random_text_selections': random_text_selections, 'random_image_selections': random_image_selections}
    headers = {
        'Authorization': 'Bearer %s' % settings.TOKEN,
        'Accept': 'application/json'
    }
    r = requests.post(url, files=files, data=data, headers=headers, timeout=15)
    if r.status_code == 201:
        return json.loads(r.text)['id']
    else:
        raise Exception("Failed creating ticket with message %s" % r.text)


phantomjs = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH, service_args=['--ignore-ssl-errors=true'])

# TODO find a way to protect resource but still be able to use PhantomJS

def render_ticket(id):
    url = "%s/tickets/%s/render/" % (settings.API_HOST, id)
    phantomjs.get(url)
    phantomjs.save_screenshot(settings.TICKET)
    return settings.TICKET







