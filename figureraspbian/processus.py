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

        # Send picture to API
        api.create_snapshot(snapshot)

        #  Render ticket
        ticket = api.render_ticket()

        # Print ticket
        devices.PRINTER.print_ticket(ticket)

        # Stop blinking
        blinking_task.terminate()

        # Set Output to True
        devices.OUTPUT.set(True)
    except Exception as e:
        print(e)



