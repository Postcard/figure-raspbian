import requests
from . import settings
from selenium import webdriver


def create_snapshot(snapshot):
    url = "%s/%s/" % (settings.API_HOST, 'snapshots')
    files = {'file': open(snapshot, 'rb')}
    data = {'scenario': settings.SCENARIO}
    headers = {'Authorization': 'Bearer %s' % settings.TOKEN}
    r = requests.post(url, files=files, data=data, headers=headers, timeout=15)
    if r.status_code != 201:
        raise Exception("Failed uploading snapshot")


phantomjs = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH, service_args=['--ignore-ssl-errors=true'])


# TODO find a way to protect resource but still be able to use PhantomJS

def render_ticket():
    url = "%s/scenarios/%s/ticket/" % (settings.API_HOST, settings.SCENARIO)
    phantomjs.get(url)
    phantomjs.save_screenshot(settings.TICKET)
    return settings.TICKET







