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
        return json.loads(r.text).id
    else:
        raise Exception("Failed creating ticket with message %s" % r.text)


phantomjs = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH, service_args=['--ignore-ssl-errors=true'])


# TODO find a way to protect resource but still be able to use PhantomJS

def render_ticket(id):
    url = "%s/scenarios/tickets/%s/render/" % (settings.API_HOST, id)
    phantomjs.get(url)
    phantomjs.save_screenshot(settings.TICKET)
    return settings.TICKET







