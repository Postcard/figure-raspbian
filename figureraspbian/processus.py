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
import cStringIO
import base64
import subprocess
import os

from . import devices, settings, ticketrenderer
from .tasks import set_paper_status, upload_ticket
from .db import Database, managed
from utils import weighted_choice
import phantomjs
from hashids import Hashids
from PIL import Image

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

                # pick a ticket template randomly
                sum_probabilities = sum(ticket_template['probability'] for
                                        ticket_template in installation.ticket_templates
                                        if 'probability' in ticket_template)
                assert 0 < sum_probabilities < 1
                equiprobable_choices = [ticket_template for
                                        ticket_template in installation.ticket_templates
                                        if 'probability' not in ticket_template]
                p = (1 - sum_probabilities) / len(equiprobable_choices)
                choices = []
                for ticket_template in installation.ticket_templates:
                    choices.append((ticket_template, ticket_template.get('probability', p)))

                ticket_template = weighted_choice(installation.ticket_templates)

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

                base64_snapshot_thumb = get_base64_snapshot_thumbnail(snapshot)

                rendered_html = ticketrenderer.render(
                    ticket_template['html'],
                    "data:image/jpeg;base64,%s" % base64_snapshot_thumb,
                    current_code,
                    date,
                    ticket_template['images'])

                del base64_snapshot_thumb

                # get ticket as base64 stream
                ticket_base64 = phantomjs.get_screenshot(rendered_html)

                # convert ticket to pure black and white

                ticket_io = base64.b64decode(ticket_base64)
                ticket = Image.open(cStringIO.StringIO(ticket_io))
                ticket = ticket.convert('1')
                ticket_path = join(settings.MEDIA_ROOT, 'ticket.png')
                ticket.save(ticket_path, ticket.format, quality=100)

                end = time.time()
                logger.info('Ticket successfully rendered in %s seconds', end - start)

                # Print ticket
                start = time.time()

                # TODO make png2pos support passing base64 file argument
                args = ['png2pos', '-r', '-s2', '-aC', ticket_path]
                my_env = os.environ.copy()
                my_env['PNG2POS_PRINTER_MAX_WIDTH'] = '576'

                p = subprocess.Popen(args, stdout=subprocess.PIPE, env=my_env)
                pos_data, err = p.communicate()

                devices.PRINTER.print_ticket(pos_data)
                end = time.time()
                logger.info('Ticket successfully printed in %s seconds', end - start)

                buf = cStringIO.StringIO()
                snapshot.save(buf, "JPEG")
                snapshot_io = buf.getvalue()
                buf.close()

                unique_id = "{hash}{resin_uuid}".format(
                    hash=hashids.encode(installation.id, int(date.strftime('%Y%m%d%H%M%S'))),
                    resin_uuid=settings.RESIN_UUID[:4]).lower()
                filename = "Figure_%s.jpg" % unique_id

                ticket = {
                    'installation': installation.id,
                    'snapshot': snapshot_io,
                    'ticket': ticket_io,
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


def get_base64_snapshot_thumbnail(snapshot):
    buf = cStringIO.StringIO()
    snapshot.resize((512, 512)).save(buf, "JPEG")
    content = base64.b64encode(buf.getvalue())
    buf.close()
    return content
