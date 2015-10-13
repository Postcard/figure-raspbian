# -*- coding: utf8 -*-
import os
import time
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from time import time

from pifacedigitalio import PiFaceDigital

from . import processus, settings, api
from .db import Database, managed

# Log configuration
settings.log_config()

pifacedigital = PiFaceDigital()

initial_input = pifacedigital.input_pins[settings.TRIGGER_PIN]
LOW = 1 if initial_input else 0
HIGH = 0 if initial_input else 1


if __name__ == '__main__':

    logger.info("Initializing Figure application...")

    logger.info("Initializing database...")
    with managed(Database()) as db:
        db.update_installation()
        db.claim_new_codes_if_necessary()

    logger.info("Downloading ticket css...")
    ticket_css_url = "%s/%s" % (settings.STATIC_HOST, 'static/css/ticket.css')
    try:
        api.download(ticket_css_url, settings.STATIC_ROOT)
        logger.info("Ready")
    except Exception:
        logger.info("An error occurred when downloading ticket css")

    try:
        prev_input = LOW
        start = None
        while True:
            curr_input = pifacedigital.input_pins[settings.TRIGGER_PIN]
            if prev_input == LOW and curr_input == HIGH:
                # Button pressed
                start = time()
            if prev_input == HIGH and curr_input == LOW:
                # Button unpressed
                delta = time() - start
                if delta > 15:
                    # TODO Unlock door
                    logger.info("Someone unlock the door...")
                    time.sleep(5)
                    # TODO Lock the door
                else:
                    logger.info("A trigger occurred ! Running processus...")
                    processus.run()
            prev_input = curr_input
            # slight pause to debounce
            time.sleep(0.05)
    except Exception as e:
        print e