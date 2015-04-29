# -*- coding: utf8 -*-

from os.path import exists, join, basename
from os import makedirs
from datetime import datetime
import time
import pytz
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import traceback
import codecs

from selenium import webdriver

from .ticketrenderer import TicketRenderer
from . import devices, settings, tasks
from .db import Database, managed


phantom_js = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)

if not exists(settings.TICKET_DIR):
    makedirs(settings.TICKET_DIR)


def run():
    with managed(Database()) as db:
        try:
            installation = db.dbroot['installation']

            if installation is not None:
                # Database is initialized !

                # check if installation is not finished
                end = datetime.strptime(installation.end, '%Y-%m-%dT%H:%M:%SZ')
                end = end.replace(tzinfo=pytz.UTC)

                if end > datetime.now(pytz.timezone(settings.TIMEZONE)):

                    # Retrieve necessary information from database
                    ticket_template = installation.ticket_template

                    # Initialize blinking task
                    blinking_task = None
                    # Set Output to False
                    devices.OUTPUT.set(True)

                    # Take a snapshot
                    start = time.time()
                    snapshot = devices.CAMERA.capture(installation.id)
                    end = time.time()
                    logger.info('Snapshot capture successfully executed in %s seconds', end - start)
                    # Start blinking
                    blinking_task = devices.OUTPUT.blink()

                    # Render ticket
                    start = time.time()
                    code = installation.get_code()
                    renderer = TicketRenderer(ticket_template['html'],
                                              ticket_template['text_variables'],
                                              ticket_template['image_variables'],
                                              ticket_template['images'])
                    html, dt, code, random_text_selections, random_image_selections = \
                        renderer.render(snapshot, code)
                    with codecs.open(settings.TICKET_HTML_PATH, 'w', 'utf-8') as ticket:
                        ticket.write(html)
                    url = "file://%s" % settings.TICKET_HTML_PATH
                    phantom_js.get(url)
                    ticket = join(settings.TICKET_DIR, basename(snapshot))
                    phantom_js.save_screenshot(ticket)
                    end = time.time()
                    logger.info('Ticket successfully rendered in %s seconds', end - start)

                    # Print ticket
                    start = time.time()
                    devices.PRINTER.print_ticket(ticket)
                    end = time.time()
                    logger.info('Ticket successfully printed in %s seconds', end - start)

                    # Stop blinking
                    blinking_task.terminate()

                    # Set Output to True
                    devices.OUTPUT.set(False)

                    # add task upload ticket task to the queue
                    ticket = {
                        'installation': installation.id,
                        'snapshot': snapshot,
                        'ticket': ticket,
                        'dt': dt,
                        'code': code,
                        'random_text_selections': random_text_selections,
                        'random_image_selections': random_image_selections,
                    }
                    db.dbroot['tickets'].add_ticket(ticket)
                else:
                    logger.warning("Current installation has ended. Skipping processus execution")
        except Exception as e:
            logger.error(e.message)
            logger.error(traceback.format_exc())
        finally:
            if 'blinking_task' in locals():
                if blinking_task is not None:
                    blinking_task.terminate()





