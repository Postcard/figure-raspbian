# -*- coding: utf8 -*-


import base64
import logging
import codecs
from signal import pause
from os import path

from gpiozero import Button
from usb.core import USBError

from ticketrenderer import TicketRenderer

from . import settings

from .utils import get_base64_snapshot_thumbnail, get_pure_black_and_white_ticket, png2pos, get_file_name
from .phantomjs import get_screenshot

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


class App(object):

    def __init__(self, camera, printer):
        self.camera = camera
        self.printer = printer
        self.button = Button(settings.BUTTON_PIN)
        ticket_template_path = path.join(settings.STATIC_ROOT, 'ticket_template.html')
        with codecs.open(ticket_template_path, 'rb', 'utf-8') as html:
            self.ticket_template_html = html.read()
        self.ticket_template = {
            'html': self.ticket_template_html,
            'title': settings.TICKET_TEMPLATE_TITLE,
            'description': settings.TICKET_TEMPLATE_DESCRIPTION,
            "text_variables": [],
            "image_variables": [],
            "images": []
        }
        self.count = 0

    def trigger(self):
        """
        This function is called when a button is pressed
        It triggers the camera and the printer
        """
        snapshot = self.camera.capture()

        media_url = 'file://%s' % settings.MEDIA_ROOT
        ticket_css_url = 'file://%s/ticket.css' % settings.STATIC_ROOT

        ticket_renderer = TicketRenderer(self.ticket_template, media_url, ticket_css_url)

        base64_snapshot_thumb = get_base64_snapshot_thumbnail(snapshot)

        rendered = ticket_renderer.render(picture="data:image/jpeg;base64,%s" % base64_snapshot_thumb)

        del base64_snapshot_thumb

        ticket_base64 = get_screenshot(rendered)
        ticket_io = base64.b64decode(ticket_base64)
        ticket_path, ticket_length = get_pure_black_and_white_ticket(ticket_io)

        pos_data = png2pos(ticket_path)

        try:
            self.printer.print_ticket(pos_data)
        except USBError:
            # Oups, it seems we are out of paper
            pass

        filename = get_file_name(self.count)

        # TODO save to USB stick
        # filepath = path.join(settings.MEDIA_ROOT, 'snapshots', filename)
        # snapshot.save()

        self.count += 1

    def run(self):
        """ Main execution loop polling for push button inputs """
        self.button.when_pressed = self.trigger
        pause()
