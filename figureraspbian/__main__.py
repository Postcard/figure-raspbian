# -*- coding: utf8 -*-

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from .app import App
import api
from db import Database, managed
import settings
from devices.camera import DSLRCamera, MockCamera
from devices.printer import EpsonPrinter
from devices.input import PiFaceDigitalInput
from devices.output import PiFaceDigitalOutput

if __name__ == '__main__':

    logger.info("Initializing database...")
    with managed(Database()) as db:
        db.update_photobooth()
        db.claim_new_codes_if_necessary()

    logger.info("Downloading ticket css...")
    ticket_css_url = "%s/%s" % (settings.STATIC_HOST, 'static/css/ticket.css')
    try:
        api.download(ticket_css_url, settings.STATIC_ROOT)
    except Exception as e:
        logger.exception(e)

    logger.info("Ready")

    try:
        try:
            camera = DSLRCamera()
        except Exception as e:
            logger.exception(e)
            camera = MockCamera()

        printer = EpsonPrinter()
        pifaceinput = PiFaceDigitalInput()
        pifaceoutput = PiFaceDigitalOutput()

        app = App(camera, printer, pifaceinput, pifaceoutput)
        app.run()
    except Exception as e:
        logger.exception(e)
        raise e



