from . import devices
from . import api


def run():
    try:
        # Set Output to False
        devices.OUTPUT.set(False)

        # Take a snapshot
        snapshot = devices.CAMERA.capture()

        # Start blinking
        blinking_task = devices.OUTPUT.blink()

        # Generate a ticket on the API and get back the id
        id = api.create_ticket(snapshot)

        #  Render ticket to image
        ticket = api.render_ticket(id)

        # Print ticket
        devices.PRINTER.print_ticket(ticket)

        # Stop blinking
        blinking_task.terminate()

        # Set Output to True
        devices.OUTPUT.set(True)
    except Exception as e:
        print(e)
    finally:
        if blinking_task:
            blinking_task.terminate()




