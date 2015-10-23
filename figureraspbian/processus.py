# -*- coding: utf8 -*-

from os.path import basename, join
import time
import random
import shutil
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from usb.core import USBError
from datetime import datetime
import pytz

from . import devices, settings, ticketrenderer
from .tasks import set_paper_status
from .db import Database, managed
import phantomjs

# Pre-calculated random_ticket to be used
code = None


def run():
    with managed(Database()) as db:
        try:
            installation = db.data.installation
            if installation.id is not None:
                # Database is initialized !

                # Take a snapshot
                start = time.time()
                snapshot = devices.CAMERA.capture(installation.id)
                end = time.time()
                logger.info('Snapshot capture successfully executed in %s seconds', end - start)

                # Render ticket

                start = time.time()
                ticket_template = random.choice(installation.ticket_templates)
                random_text_selections = [ticketrenderer.random_selection(variable) for
                                          variable in
                                          ticket_template['text_variables']]
                random_image_selections = [ticketrenderer.random_selection(variable) for
                                           variable in
                                           ticket_template['image_variables']]

                global code
                if code:
                    current_code = code
                else:
                    # we need to claim a code
                    start = time.time()
                    current_code = db.get_code()
                    end = time.time()
                    logger.info('Successfully claimed code in %s seconds', end - start)

                date = datetime.now(pytz.timezone(settings.TIMEZONE))

                rendered_html = ticketrenderer.render(
                    ticket_template['html'],
                    "data:image/jpeg;base64;%s" % snapshot,
                    current_code,
                    date,
                    ticket_template['images'],
                    random_text_selections,
                    random_image_selections)

                # get ticket as base64 stream
                ticket_data = phantomjs.get_screenshot(rendered_html)

                end = time.time()
                logger.info('Ticket successfully rendered in %s seconds', end - start)

                # Print ticket
                start = time.time()
                devices.PRINTER.print_ticket(ticket_data)
                end = time.time()
                logger.info('Ticket successfully printed in %s seconds', end - start)

                # TODO asynchronous task to upload snapshot and ticket
                # TODO if this fails, write image to disk and add it to the queue

                # Save ticket to disk
                # ticket_path = join(settings.MEDIA_ROOT, 'tickets', basename(snapshot_raspberry_path))
                # with open(ticket_path, "wb") as f:
                #     f.write(ticket_data.decode('base64'))

                # Get good quality image in order to upload it
                # snapshot.thumbnail((1024, 1024), Image.ANTIALIAS)
                # snapshot.save(snapshot_raspberry_path)
                # if settings.BACKUP_ON:
                #     shutil.copy2(snapshot_raspberry_path, "/mnt/%s" % basename(snapshot_raspberry_path))

                # add task upload ticket task to the queue
                # ticket = {
                #     'installation': installation.id,
                #     'snapshot': snapshot_raspberry_path,
                #     'ticket': ticket_path,
                #     'dt': date,
                #     'code': current_code,
                #     'random_text_selections': random_text_selections,
                #     'random_image_selections': random_image_selections
                # }
                # db.add_ticket(ticket)

                # Calculate random snapshot path
                # random_ticket = db.get_random_ticket()
                # random_snapshot_path = random_ticket['snapshot'] if random_ticket else None

                # Calculate new code
                start = time.time()
                code = db.get_code()
                db.claim_new_codes_if_necessary()
                end = time.time()
                logger.info('Successfully claimed code in %s seconds', end - start)
                set_paper_status.delay('1')

            else:
                logger.warning("No active installation. Skipping processus execution")
        except USBError:
            # There is no paper
            set_paper_status.delay('0')
        except Exception as e:
            logger.exception(e)