# -*- coding: utf8 -*-

import time
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

import pifacedigitalio

from . import processus, settings, utils
from .db import Database, managed

# Log configuration
settings.log_config()

refresh_listener = False


def trigger(event):
    logger.info("A trigger occurred ! Running processus...")
    processus.run()
    global refresh_listener
    refresh_listener = True

pifacedigital = pifacedigitalio.PiFaceDigital()


def get_listener():
    l = pifacedigitalio.InputEventListener(chip=pifacedigital)
    l.register(settings.TRIGGER_PIN, pifacedigitalio.IODIR_RISING_EDGE, trigger, 100)
    l.activate()
    return l


if __name__ == '__main__':

    logger.info("Initializing Figure application...")

    logger.info("Initializing database...")
    database = Database()
    database.open()
    database.close()

    listener = get_listener()

    try:
        while True:
            if refresh_listener:
                listener.deactivate()
                listener = get_listener()
                refresh_listener = False
            time.sleep(1)
    except Exception as e:
        print e
    finally:
        listener.deactivate()


