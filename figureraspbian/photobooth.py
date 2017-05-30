# -*- coding: utf8 -*-

from datetime import datetime
import pytz
import cStringIO
import logging
from threading import Thread
import time
from os import path

from ticketrenderer import TicketRenderer
from PIL import Image

from models import Code, Photobooth as PhotoboothModel
import settings
import utils
from decorators import execute_if_not_busy
from exceptions import OutOfPaperError, DevicesBusy, PhotoboothNotReady
import request
from devices.camera import Camera
from devices.printer import Printer
from devices.door_lock import DoorLock
from threads import rlock
import webkit2png


logger = logging.getLogger(__name__)


class Photobooth(object):

    def __init__(self):
        # data
        self.photobooth = PhotoboothModel.get()
        self.context = None
        self.update_dict = {}
        # devices
        self.camera = self.printer = self.door_lock = None
        self.ready = False
        self.initialize_devices()
        if self.camera and self.printer:
            self.ready = True

    def initialize_devices(self):
        self.camera = Camera.factory()
        if self.camera:
            self.camera.clear_space()
        self.printer = Printer.factory()
        self.door_lock = DoorLock.factory()

    def trigger(self):
        if self.ready:
            try:
                return self._trigger()
            except DevicesBusy:
                pass
        else:
            raise PhotoboothNotReady()

    @execute_if_not_busy(rlock)
    def _trigger(self):
        self.photobooth = PhotoboothModel.get()
        if self.photobooth.paper_level == 0:
            # check if someone has refilled the paper
            paper_present = self.printer.paper_present()
            if not paper_present:
                return
        picture = self.camera.capture()
        return self.render_print_and_upload(picture)

    def render_print_and_upload(self, picture):
        self.set_context()
        html = self.render_ticket(picture)
        ticket = webkit2png.get_screenshot(html)
        try:
            ticket = self.printer.prepare_image(ticket)
            ticket_length = self.printer.print_image(ticket)
            self.update_dict['paper_level'] = utils.new_paper_level(self.paper_level, ticket_length)
        except OutOfPaperError:
            logger.info("The printer is out of paper")
            self.update_dict['paper_level'] = 0
        filename = utils.get_file_name(self.context['code'])

        portrait = {
            'picture': picture,
            'ticket': ticket,
            'taken': self.context['date'],
            'place': self.place.id if self.place else None,
            'event': self.event.id if self.event else None,
            'photobooth': self.id,
            'code': self.context['code'],
            'filename': filename
        }

        q = PhotoboothModel.update(counter=PhotoboothModel.counter + 1, **self.update_dict)
        q = q.where(PhotoboothModel.uuid == settings.RESIN_UUID)
        q.execute()
        self.photobooth = PhotoboothModel.get()

        request.upload_portrait_async(portrait)
        request.update_paper_level_async(self.paper_level)

        return ticket

    def trigger_async(self):
        thr = Thread(target=self.trigger, args=(), kwargs={})
        thr.start()
        return thr

    def set_context(self):
        """ returns the context used to generate a ticket from a ticket template """
        code = Code.pop()
        tz = self.place.tz if self.place else settings.DEFAULT_TIMEZONE
        date = datetime.now(pytz.timezone(tz))
        counter = self.counter
        self.context = {'code': code, 'date': date, 'counter': counter}

    def render_ticket(self, picture):
        ticket_renderer = TicketRenderer(
            self.ticket_template.serialize(),
            settings.MEDIA_URL,
            settings.LOCAL_TICKET_CSS_URL)
        # resize picture
        w = h = settings.TICKET_TEMPLATE_PICTURE_SIZE
        pil_picture = Image.open(cStringIO.StringIO(picture))
        resized = pil_picture.resize((w, h))
        resized.format = pil_picture.format
        data_url = utils.get_data_url(resized)
        html = ticket_renderer.render(data_url, **self.context)
        return html

    def unlock_door(self):
        self.door_lock.open()
        time.sleep(settings.DOOR_OPENING_TIME)
        self.door_lock.close()

    def print_booting_ticket(self):
        if self.ready:
            booting_template_path = path.join(settings.STATIC_ROOT, 'booting.html')
            tz = self.place.tz if self.place else settings.DEFAULT_TIMEZONE
            rendered = utils.render_jinja_template(
                booting_template_path,
                css_url=settings.LOCAL_TICKET_CSS_URL,
                logo_url=settings.LOCAL_LOGO_FIGURE_URL,
                date=datetime.now(pytz.timezone(tz)).strftime('%d/%m/%Y %H:%M'),
                serial_number=self.serial_number,
                place=self.place.name if self.place else None,
                event=self.event.name if self.event else None,
                is_online=request.is_online()
            )
            ticket = webkit2png.get_screenshot(rendered)
            ticket = self.printer.prepare_image(ticket)
            self.printer.print_image(ticket)

    @property
    def id(self):
        return self.photobooth.id

    @property
    def serial_number(self):
        return self.photobooth.serial_number

    @property
    def place(self):
        return self.photobooth.place

    @property
    def event(self):
        return self.photobooth.event

    @property
    def ticket_template(self):
        return self.photobooth.ticket_template

    @property
    def counter(self):
        return self.photobooth.counter

    @counter.setter
    def counter(self, value):
        self.photobooth.counter = value

    @property
    def paper_level(self):
        return self.photobooth.paper_level

    @paper_level.setter
    def paper_level(self, value):
        self.photobooth.paper_level = value



_photobooth = None


def get_photobooth():
    """ Instantiate photobooth lazily """
    global _photobooth
    if not _photobooth:
        _photobooth = Photobooth()
    return _photobooth