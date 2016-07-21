# -*- coding: utf8 -*-
import logging

from figureraspbian import photobooth
from figureraspbian import settings
from figureraspbian.devices.button import PiFaceDigitalButton
from figureraspbian import db

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


class App(object):
    """
    Registers button callbacks and make sure resources are correctly initialized and closed
    """

    def __init__(self):
        db.init()
        photobooth.initialize()
        self.button = PiFaceDigitalButton(settings.BUTTON_PIN, 0.05, settings.DOOR_OPENING_DELAY)
        self.button.when_pressed = self.when_pressed
        self.button.when_held = self.when_held
        self.intervals = photobooth.set_intervals()

    def when_pressed(self):
        photobooth.trigger_async()

    def when_held(self):
        photobooth.unlock()

    def start(self):
        self.button.start()
        logger.info("Ready...")

    def stop(self):
        db.close()
        for interval in self.intervals:
            interval.stop()
        self.button.close()
        # wait for a trigger to complete before exiting
        photobooth.lock.acquire()
        logger.info("Bye Bye")



