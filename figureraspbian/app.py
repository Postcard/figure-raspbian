# -*- coding: utf8 -*-

import time
from datetime import datetime
import pytz
import cStringIO
import base64
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import transaction

from usb.core import USBError

from ticketrenderer import TicketRenderer

from . import settings
from .db import Database, managed
from .tasks import upload_portrait, set_paper_level
from .utils import get_base64_snapshot_thumbnail, get_pure_black_and_white_ticket, png2pos, get_file_name
from .phantomjs import get_screenshot


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
                        if settings.DOOR_OPENING_DELAY < elapsed < settings.DOOR_OPENING_DELAY + 5:
                            logger.info("Someone unlocked the door...")
                            self.is_door_open = True
                            self.output.turn_on()
                            time.sleep(settings.DOOR_OPENING_TIME)
                            self.output.turn_off()

                if curr_input == settings.INPUT_LOW and self.prev_input == settings.INPUT_HIGH:
                    # Button unpressed
                    logger.info("A trigger occurred !")

                    transaction.commit()

                    photobooth = db.get_photobooth()
                    ticket_template = photobooth.ticket_template

                    place = photobooth.place
                    place_id = place['id'] if place else None
                    tz = place['tz'] if (place and 'tz' in place) else settings.DEFAULT_TIMEZONE

                    event_id = photobooth.event['id'] if photobooth.event else None

                    if ticket_template:

                        snapshot = self.camera.capture()

                        media_url = 'file://%s' % settings.MEDIA_ROOT
                        ticket_css_url = 'file://%s/ticket.css' % settings.STATIC_ROOT

                        ticket_renderer = TicketRenderer(ticket_template, media_url, ticket_css_url)

                        current_code = self.code or db.get_code()
                        date = datetime.now(pytz.timezone(tz))
                        base64_snapshot_thumb = get_base64_snapshot_thumbnail(snapshot)

                        rendered = ticket_renderer.render(
                            picture="data:image/jpeg;base64,%s" % base64_snapshot_thumb,
                            code=current_code,
                            date=date)

                        del base64_snapshot_thumb

                        ticket_base64 = get_screenshot(rendered)
                        ticket_io = base64.b64decode(ticket_base64)
                        ticket_path, ticket_length = get_pure_black_and_white_ticket(ticket_io)

                        pos_data = png2pos(ticket_path)

                        try:
                            self.printer.print_ticket(pos_data)
                            new_paper_level = db.get_new_paper_level(ticket_length)
                            set_paper_level.delay(new_paper_level)
                        except USBError:
                            # Oups, it seems we are out of paper
                            new_paper_level = db.get_new_paper_level(0)
                            set_paper_level.delay(new_paper_level)
                        buf = cStringIO.StringIO()
                        snapshot.save(buf, "JPEG")
                        picture_io = buf.getvalue()
                        buf.close()

                        filename = get_file_name(current_code)

                        portrait = {
                            'picture': picture_io,
                            'ticket': ticket_io,
                            'taken': date,
                            'place': place_id,
                            'event': event_id,
                            'photobooth': photobooth.id,
                            'code': current_code,
                            'filename': filename,
                            'is_door_open': self.is_door_open
                        }

                        self.is_door_open = False
                        self.code = db.get_code()

                        db.claim_new_codes_if_necessary()
                        upload_portrait.delay(portrait)

                    else:
                        logger.info("Could not find any ticket template")

                if curr_input == -1:
                    # used to break the loop during test execution
                    break

                # slight pause to debounce
                time.sleep(0.05)
                self.prev_input = curr_input
