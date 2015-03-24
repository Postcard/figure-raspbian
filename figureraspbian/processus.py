from . import devices, api, settings
from selenium import webdriver
from os.path import exists, join, basename
from os import makedirs
from .ticketrenderer import TicketRenderer
import tasks


phantom_js = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)

if not exists(settings.TICKET_DIR):
    makedirs(settings.TICKET_DIR)

# get a database object and try updating
database = Database(settings.ENVIRONMENT)
database.update()

def run():
    try:
        # Initialize blinking task
        blinking_task = None

        # Set Output to False
        devices.OUTPUT.set(True)

        # Take a snapshot
        snapshot = devices.CAMERA.capture()

        # Start blinking
        blinking_task = devices.OUTPUT.blink()

        # Render ticket
        t = database.ticket_template()
        renderer = TicketRenderer(t.html, t.text_variables, t.image_variables, t.images)
        html, datetime, code, random_text_selections, random_image_selections = renderer.render(snapshot)
        with open(settings.TICKET_HTML_PATH, 'w') as ticket:
            ticket.write(html)
        url = "file://%s" + settings.TICKET_HTML_PATH
        phantom_js.get(url)
        ticket = join(settings.TICKET_DIR, basename(snapshot))
        phantom_js.save_screenshot(ticket)

        # Print ticket
        devices.PRINTER.print_ticket(ticket)

        # Stop blinking
        blinking_task.terminate()

        # Set Output to True
        devices.OUTPUT.set(False)

        # add task upload ticket task to the queue

        tasks.create_ticket(snapshot, ticket, datetime, code, random_text_selections, random_image_selections)

    except Exception as e:
        print(e)
    finally:
        if blinking_task:
            blinking_task.terminate()




