# -*- coding: utf8 -*-
from flask import Flask
import psutil
import gunicorn.app.base
from gunicorn.six import iteritems

from figureraspbian import photobooth
from figureraspbian import db, settings

app = Flask(__name__)


@app.route('/trigger')
def trigger():
    return photobooth.trigger()


@app.route('/info')
def info():
    photobooth = db.get_photobooth()
    place = photobooth.place.name if photobooth.place else ''
    identifier = photobooth.serial_number or settings.RESIN_UUID
    number_of_portraits_to_be_uploaded = db.get_portrait_to_be_uploaded() or 0
    html = u"""
    <h1>Figure photobooth {identifier}</h1>
    </br>
    <p>Place: {place}</p>
    <p>Photo counter: </p>
    <p>Number of portraits to be uploaded: {number_of_portraits_to_be_uploaded}<p>
    """.format(
        identifier=identifier,
        place=place,
        number_of_portraits_to_be_uploaded=number_of_portraits_to_be_uploaded
    )
    return html


@app.route('/system')
def system():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_usage_percent = psutil.disk_usage('/').percent
    number_of_processes = len(psutil.pids())
    html = u"""
    <p>cpu: {cpu_percent}%</p>
    <p>memory: {memory_percent}%</p>
    <p>disk_usage: {disk_usage_percent}%</p>
    <p>number of processes: {number_of_processes}</p>
    """.format(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_usage_percent=disk_usage_percent,
        number_of_processes=number_of_processes
    )
    return html


@app.route('/acquire_lock')
def acquire_lock():
    return photobooth.lock.acquire(False)


@app.route('/release_lock')
def release_lock():
    try:
        photobooth.lock.release()
    except Exception:
        pass
    finally:
        return "Lock released"


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def start_server():
    options = {
        'bind': '%s:%s' % ('0.0.0.0', '80'),
        'workers': 4,
    }
    StandaloneApplication(app, options).run()






