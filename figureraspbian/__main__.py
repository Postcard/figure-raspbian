# -*- coding: utf8 -*-

import logging
import signal

from figureraspbian.app import App

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


class GracefulKiller:

    kill_now = False

    def __init__(self, app):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.app = app

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        self.app.stop()


if __name__ == '__main__':

    app = App()
    app.start()
    killer = GracefulKiller(app)
    signal.pause()




