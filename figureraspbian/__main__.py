# -*- coding: utf8 -*-

import signal
import os
import logging

import requests

from app import App
from db import db
from devices.button import Button
import settings
from models import get_all_models, Photobooth


logging.basicConfig(format=settings.LOG_FORMAT, datefmt='%Y.%m.%d %H:%M:%S', level='INFO')


class GracefulKiller:

    kill_now = False

    def __init__(self, app):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.app = app

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        self.app.stop()
        db.close_db()


class ShutdownHook:

    def __init__(self):
        self.shutdown_button = Button.factory(settings.SHUTDOWN_PIN, 0.05, 10, False)
        self.shutdown_button.when_pressed = self.shutdown

    def shutdown(self):
        # Call resin.io supervisor shutdown endpoint https://docs.resin.io/runtime/supervisor-api/#post-v1-shutdown
        resin_supervisor_address = settings.RESIN_SUPERVISOR_ADDRESS
        resin_supervisor_api_key = settings.RESIN_SUPERVISOR_API_KEY
        shutdown_url = "%s/v1/shutdown?apikey=%s" % (resin_supervisor_address, resin_supervisor_api_key)
        requests.post(shutdown_url, data={'force': True})


def create_tables():
    db.connect_db()
    # creates tables if not exist
    db.database.create_tables(get_all_models(), True)

if __name__ == '__main__':

    create_tables()
    Photobooth.get_or_create(uuid=settings.RESIN_UUID)
    app = App()
    killer = GracefulKiller(app)
    app.start()
    shutdown_hook = ShutdownHook()
    signal.pause()






