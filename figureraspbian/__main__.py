# -*- coding: utf8 -*-
import os
import time
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

import time

from pifacedigitalio import PiFaceDigital

from . import processus, settings, api
from .db import Database, managed

# Log configuration
settings.log_config()

pifacedigital = PiFaceDigital()


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
        initial_input = pifacedigital.input_pins[settings.TRIGGER_PIN].value
        LOW = 1 if initial_input else 0
        HIGH = 0 if initial_input else 1

        prev_input = LOW
        start = None
        while True:
            curr_input = pifacedigital.input_pins[settings.TRIGGER_PIN].value
            if curr_input == HIGH:
                # Button pressed
                if prev_input == LOW:
                    start = time.time()
                else:
                    delta = time.time() - start
                    if delta > 15:
                        logger.info("Someone unlock the door...")
                        pifacedigital.relays[0].turn_on()
                        time.sleep(5)
                        pifacedigital.relays[0].turn_off()

            if curr_input == LOW and prev_input == HIGH:
                # Button unpressed
                logger.info("A trigger occurred ! Running processus...")
                processus.run()
            prev_input = curr_input
            # slight pause to debounce
            time.sleep(0.05)
    except Exception as e:
        logger.error(e.message)