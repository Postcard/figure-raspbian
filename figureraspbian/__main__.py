# -*- coding: utf8 -*-

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from .app import App
from devices.camera import DSLRCamera
from devices.printer import EpsonPrinter

if __name__ == '__main__':

    logger.info("Starting app")

    try:

        camera = DSLRCamera()
        printer = EpsonPrinter()

        app = App(camera, printer)
        app.run()
    except Exception as e:
        logger.exception(e)
        raise e



