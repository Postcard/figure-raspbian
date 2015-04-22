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

    logger.info("Checking utf8 configuration...")
    decoded = "é".decode('utf-8')
    logger.info("My awesome utf-8 character is %s" % decoded)


    # Make sure database is correctly initialized
    with managed(Database()) as db:
        if utils.internet_on():
            logging.info("Got an internet connection. Initializing database...")
            db.update()
        elif db.is_initialized():
            logging.info("No internet connection but database was already initialized during a previous runtime")
            pass
        else:
            logging.warning("Database could not be initialized.")

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


