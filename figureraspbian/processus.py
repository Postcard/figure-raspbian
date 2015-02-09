import logging
from . import devices
from . import api

logger = logging.getLogger(__name__)

def run():
    try:
        # Set Output to False
        devices.OUTPUT.set(False)

        # Take a snapshot
        snapshot = devices.CAMERA.capture()

        # Start blinking
        devices.OUTPUT.blink()

        # Send picture to API
        api.create_snapshot(snapshot)

        #  Render ticket
        ticket = api.render_ticket()

        # Print ticket
        devices.PRINTER.print_ticket(ticket)

        # Set Output to True
        devices.output.set(True)
    except Exception as e:
        logger.error(e)



