# -*- coding: utf8 -*-

from os.path import basename, join
import time
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import codecs
from PIL import Image

from .ticketrenderer import TicketRenderer
from . import devices, settings
from .db import Database, managed
import phantomjs


def run():
    with managed(Database()) as db:
        try:
            installation = db.data.installation

            if installation.id is not None:
                # Database is initialized !

                # Retrieve necessary information from database
                ticket_template = installation.ticket_template

                # Initialize blinking task
                blinking_task = None
                # Set Output to False
                devices.OUTPUT.set(True)

                # Take a snapshot
                start = time.time()
                snapshot_path, snapshot = devices.CAMERA.capture(installation.id)
                end = time.time()
                logger.info('Snapshot capture successfully executed in %s seconds', end - start)
                # Start blinking
                blinking_task = devices.OUTPUT.blink()

                # Render ticket
                start = time.time()
                code = db.get_code()
                renderer = TicketRenderer(ticket_template['html'],
                                          ticket_template['text_variables'],
                                          ticket_template['image_variables'],
                                          ticket_template['images'])
                html, dt, code, random_text_selections, random_image_selections = \
                    renderer.render(snapshot_path, code)
                ticket_html_path = join(settings.STATIC_ROOT, 'ticket.html')
                with codecs.open(ticket_html_path, 'w', 'utf-8') as ticket_html:
                    ticket_html.write(html)

                # get ticket as base64 stream
                ticket_data = phantomjs.get_screenshot()

                end = time.time()
                logger.info('Ticket successfully rendered in %s seconds', end - start)

                # Print ticket
                start = time.time()
                devices.PRINTER.print_ticket(ticket_data)
                end = time.time()
                logger.info('Ticket successfully printed in %s seconds', end - start)

                # Stop blinking
                blinking_task.terminate()

                # Set Output to True
                devices.OUTPUT.set(False)

                # Save ticket to disk
                ticket_path = join(settings.MEDIA_ROOT, 'tickets', basename(snapshot_path))
                with open(ticket_path, "wb") as f:
                    f.write(ticket_data.decode('base64'))

                # Get good quality image in order to upload it
                snapshot.thumbnail((1024, 1024), Image.ANTIALIAS)
                snapshot.save(snapshot_path)

                # add task upload ticket task to the queue
                ticket = {
                    'installation': installation.id,
                    'snapshot': snapshot_path,
                    'ticket': ticket_path,
                    'dt': dt,
                    'code': code,
                    'random_text_selections': random_text_selections,
                    'random_image_selections': random_image_selections
                }
                db.add_ticket(ticket)
            else:
                logger.warning("Current installation has ended. Skipping processus execution")
        except Exception as e:
            logger.exception(e)
        finally:
            if 'blinking_task' in locals():
                if blinking_task is not None:
                    blinking_task.terminate()





