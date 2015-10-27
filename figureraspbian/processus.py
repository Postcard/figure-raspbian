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
from .tasks import set_paper_status, upload_ticket
from .db import Database, managed
import phantomjs
from hashids import Hashids

hashids = Hashids(salt='Titi Vicky Benni')

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
                    "data:image/png;base64,%s" % snapshot,
                    current_code,
                    date,
                    ticket_template['images'],
                    random_text_selections,
                    random_image_selections)

                # get ticket as base64 stream
                ticket = phantomjs.get_screenshot(rendered_html)

                end = time.time()
                logger.info('Ticket successfully rendered in %s seconds', end - start)

                # Print ticket
                start = time.time()
                devices.PRINTER.print_ticket(ticket)
                end = time.time()
                logger.info('Ticket successfully printed in %s seconds', end - start)

                unique_id = "{hash}{resin_uuid}".format(
                    hash=hashids.encode(installation.id, int(date.strftime('%Y%m%d%H%M%S'))),
                    resin_uuid=settings.RESIN_UUID[:4]).lower()
                filename = "Figure_%s.jpg" % unique_id

                ticket = {
                    'installation': installation.id,
                    'snapshot': snapshot,
                    'ticket': ticket,
                    'dt': date,
                    'code': current_code,
                    'filename': filename
                }

                upload_ticket.delay(ticket)

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