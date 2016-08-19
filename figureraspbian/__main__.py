# -*- coding: utf8 -*-

import signal

from figureraspbian.app import App

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
    killer = GracefulKiller(app)
    app.start()
    signal.pause()






