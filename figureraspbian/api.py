import requests
from . import settings
from selenium import webdriver

s = requests.Session()
s.headers.update({'Authorization': 'Bearer %s' % settings.TOKEN})

def create_snapshot(snapshot):
    url = "%s/%s" % (settings.API_HOST, 'snapshots')
    files = {'file': open(snapshot, 'rb')}
    data = {'scenario': settings.SCENARIO}
    r = requests.post(url, files=files, data=data, timeout=15)
    if r.status_code != 200:
        raise Exception("Failed uploading snapshot")


phantomjs = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)

# TODO find a way to protect resource but still be able to use PhantomJS

def render_ticket():
    url = "%s/scenarios/%s/ticket" % (settings.API_HOST, settings.SCENARIO)
    phantomjs.get(url)
    phantomjs.save_screenshot(settings.TICKET)
    return settings.TICKET







