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
from .tasks import upload_ticket

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

    prev_input = settings.INPUT_LOW
    start = None
    is_door_open = False

    while True:
        try:
            curr_input = pifacedigital.input_pins[settings.TRIGGER_PIN].value
            if curr_input == settings.INPUT_HIGH:
                # Button pressed
                if prev_input == settings.INPUT_LOW:
                    start = time.time()
                else:
                    delta = time.time() - start
                    if 15 < delta < 20:
                        logger.info("Someone unlocked the door...")
                        pifacedigital.relays[0].turn_on()
                        is_door_open = True
                        time.sleep(5)
                        pifacedigital.relays[0].turn_off()

            if curr_input == settings.INPUT_LOW and prev_input == settings.INPUT_HIGH:
                # Button unpressed
                logger.info("A trigger occurred ! Running processus...")
                ticket = processus.run()
                ticket['is_door_open'] = is_door_open
                is_door_open = False
                upload_ticket.delay(ticket)
            prev_input = curr_input
            # slight pause to debounce
            time.sleep(0.05)
        except Exception as e:
            logger.error(e.message)
            time.sleep(5)