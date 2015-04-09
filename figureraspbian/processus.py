from selenium import webdriver
from os.path import exists, join, basename
from os import makedirs
from datetime import datetime
import pytz
from .ticketrenderer import TicketRenderer
from . import devices, settings
from .db import Database, managed
import tasks


phantom_js = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)

if not exists(settings.TICKET_DIR):
    makedirs(settings.TICKET_DIR)


def run():
    try:
        with managed(Database(settings.ENVIRONMENT)) as db:

            # check if installation is not finished
            end = datetime.strptime(db.installation()['end'], '%Y-%m-%dT%H:%M:%SZ')

            if end > datetime.now(pytz.timezone(settings.TIMEZONE)):

                # Initialize blinking task
                blinking_task = None
                # Set Output to False
                devices.OUTPUT.set(True)

                # Take a snapshot
                snapshot = devices.CAMERA.capture()
                # Start blinking
                blinking_task = devices.OUTPUT.blink()

                # Render ticket
                t = db.ticket_template()
                renderer = TicketRenderer(t['html'], t['text_variables_objects'], t['image_variables_objects'],
                                          t['images_objects'])
                html, dt, code, random_text_selections, random_image_selections = renderer.render(snapshot)
                with open(settings.TICKET_HTML_PATH, 'w') as ticket:
                    ticket.write(html)
                url = "file://%s" % settings.TICKET_HTML_PATH
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
                tasks.create_ticket.delay(snapshot, ticket, dt, code, random_text_selections, random_image_selections)
            else:
                print "Skip processus. Installation is ended"
    except Exception as e:
        print(e)
    finally:
        if 'blinking_task' in locals():
            if blinking_task is not None:
                blinking_task.terminate()





