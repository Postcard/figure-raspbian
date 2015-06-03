# -*- coding: utf8 -*-

from os.path import basename, join
import time
import shutil
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import io
from PIL import Image

from . import devices, settings, ticketrenderer
from .db import Database, managed
import phantomjs

# Pre-calculated random_ticket to be used
random_snapshot_path = None
code = None

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
                snapshot_path, snapshot, date = devices.CAMERA.capture(installation.id)
                end = time.time()
                logger.info('Snapshot capture successfully executed in %s seconds', end - start)
                # Start blinking
                blinking_task = devices.OUTPUT.blink()

                # Render ticket

                start = time.time()
                random_text_selections = [ticketrenderer.random_selection(variable) for
                                          variable in
                                          ticket_template['text_variables']]
                random_image_selections = [ticketrenderer.random_selection(variable) for
                                           variable in
                                           ticket_template['image_variables']]

                if code:
                    current_code = code
                else:
                    # we need to claim a code
                    start = time.time()
                    current_code = db.get_code()
                    end = time.time()
                    logger.info('Successfully claimed code in %s seconds', end - start)

                rendered_html = ticketrenderer.render(
                    ticket_template['html'],
                    snapshot_path,
                    random_snapshot_path,
                    current_code,
                    date,
                    ticket_template['images'],
                    random_text_selections,
                    random_image_selections)
                ticket_html_path = join(settings.STATIC_ROOT, 'ticket.html')

                with io.open(ticket_html_path, mode='w', encoding='utf-8') as ticket_html:
                    ticket_html.write(rendered_html)

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
                if settings.BACKUP_ON:
                    shutil.copy2(snapshot_path, "/mnt/%s" % basename(snapshot_path))

                # Calculate random snapshot path
                global random_snapshot_path
                random_ticket = db.get_random_ticket()
                random_snapshot_path = random_ticket['snapshot'] if random_ticket else None

                # Calculate new code
                start = time.time()
                global code
                code = db.get_code()
                end = time.time()
                logger.info('Successfully claimed code in %s seconds', end - start)

                # add task upload ticket task to the queue
                ticket = {
                    'installation': installation.id,
                    'snapshot': snapshot_path,
                    'ticket': ticket_path,
                    'dt': date,
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





