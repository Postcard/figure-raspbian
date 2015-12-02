# -*- coding: utf8 -*-

import time
from datetime import datetime
import pytz
import cStringIO
import base64
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from usb.core import USBError

from . import settings, ticketpicker
from .db import Database, managed, PAPER_OK, PAPER_EMPTY
from .tasks import upload_ticket, set_paper_status
from .utils import get_base64_snapshot_thumbnail, get_pure_black_and_white_ticket, png2pos, get_file_name
from .phantomjs import get_screenshot
from ticketrenderer import render


class App(object):

    def __init__(self, camera, printer, input, output):
        self.camera = camera
        self.printer = printer
        self.input = input
        self.output = output
        self.prev_input = settings.INPUT_LOW
        self.timer = None
        self.code = None
        self.is_door_open = False

    def run(self):
        """ Main execution loop polling for push button inputs """

        with managed(Database()) as db:

            while True:

                curr_input = self.input.get_value()

                if curr_input == settings.INPUT_HIGH:
                    # Button pressed
                    if self.prev_input == settings.INPUT_LOW:
                        self.timer = time.time()
                    else:
                        elapsed = time.time() - self.timer
                        if 15 < elapsed < 20:
                            logger.info("Someone unlocked the door...")
                            self.is_door_open = True
                            self.output.turn_on()
                            time.sleep(5)
                            self.output.turn_off()

                if curr_input == settings.INPUT_LOW and self.prev_input == settings.INPUT_HIGH:
                    # Button unpressed
                    logger.info("A trigger occurred !")

                    installation = db.get_installation()

                    if installation and installation.ticket_templates:

                        time.sleep(settings.CAPTURE_DELAY)
                        snapshot = self.camera.capture()
                        ticket_template = ticketpicker.weighted_choice(installation.ticket_templates)

                        current_code = self.code or db.get_code()
                        date = datetime.now(pytz.timezone(settings.TIMEZONE))
                        base64_snapshot_thumb = get_base64_snapshot_thumbnail(snapshot)

                        # TODO render PAPER END message if settings.PAPER_ROLL_LENGTH - printed_paper_length < threshold

                        rendered_html = render(
                            ticket_template['html'],
                            "data:image/jpeg;base64,%s" % base64_snapshot_thumb,
                            current_code,
                            date,
                            ticket_template['images'])

                        del base64_snapshot_thumb

                        ticket_base64 = get_screenshot(rendered_html)
                        ticket_io = base64.b64decode(ticket_base64)
                        ticket_path, ticket_length = get_pure_black_and_white_ticket(ticket_io)

                        pos_data = png2pos(ticket_path)

                        try:
                            self.printer.print_ticket(pos_data)
                            prev_paper_status = db.get_paper_status()
                            db.set_paper_status(PAPER_OK)
                            if prev_paper_status == PAPER_EMPTY:
                                db.set_printed_paper_length(ticket_length)
                            else:
                                db.add_printed_paper_length(ticket_length)
                            set_paper_status.delay(str(PAPER_OK), db.get_printed_paper_length())

                        except USBError:
                            # we are out of paper
                            db.set_paper_status(PAPER_EMPTY)
                            set_paper_status.delay(str(PAPER_EMPTY), db.get_printed_paper_length())

                        buf = cStringIO.StringIO()
                        snapshot.save(buf, "JPEG")
                        snapshot_io = buf.getvalue()
                        buf.close()

                        filename = get_file_name(installation.id, date)

                        ticket = {
                            'installation': installation.id,
                            'snapshot': snapshot_io,
                            'ticket': ticket_io,
                            'dt': date,
                            'code': current_code,
                            'filename': filename,
                            'is_door_open': self.is_door_open
                        }
                        self.is_door_open = False
                        self.code = db.get_code()

                        db.claim_new_codes_if_necessary()
                        upload_ticket.delay(ticket)

                    else:
                        logger.info("Could not find any installation or ticket templates")

                if curr_input == -1:
                    # used to break the loop during test execution
                    break

                # slight pause to debounce
                time.sleep(0.05)
                self.prev_input = curr_input
