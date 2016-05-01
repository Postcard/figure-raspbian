# -*- coding: utf8 -*-

from contextlib import contextmanager
import logging
import time
import os
import errno
import figure

from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError
import transaction
import persistent
import urllib2

from . import settings, api
from .utils import timeit, pixels2cm

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

figure.api_base = settings.API_HOST
figure.token = settings.TOKEN


@contextmanager
def managed(database):
    database.open()
    yield database
    database.close()


def transaction_decorate(retry_delay=1):
    def wrap(func):
        def wrapped_f(self, *args, **kwargs):
            while True:
                try:
                    result = func(self, *args, **kwargs)
                    transaction.commit()
                except ConflictError:
                    # Conflict occurred; this process should abort,
                    # wait for a little bit, then try again.
                    transaction.abort()
                    time.sleep(retry_delay)
                else:
                    # No ConflictError exception raised, so break
                    # out of the enclosing while loop.
                    return result
        return wrapped_f
    return wrap


IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, 'images')
DATABASE_VERSION = 10


class Database(object):
    """ Handle retrieving and updating data"""

    def __init__(self):
        self.storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(self.storage)
        self.dbroot = self.db.open().root()
        if 'data' not in self.dbroot:
            self.dbroot['data'] = Data()
            transaction.commit()
        # If local database is outdated, create a brand new one
        if not hasattr(self.dbroot['data'], 'version') or self.dbroot['data'].version < DATABASE_VERSION:
            self.clear()
        self.data = self.dbroot['data']

    def open(self):
        pass

    def close(self):
        self.db.close()

    @transaction_decorate(5)
    def clear(self):
        self.dbroot['data'] = Data()

    def get_photobooth(self):
        return self.data.photobooth

    def set_ticket_template(self, ticket_template):
        try:
            local_items = self.get_images_from_ticket_template(self.data.photobooth.ticket_template)
            items = self.get_images_from_ticket_template(ticket_template)
            # Download all images that have not been previously downloaded
            images_to_download = list(set(items) - set(local_items))
            for image in images_to_download:
                api.download(image, IMAGE_DIR)
            self.data.photobooth.ticket_template = ticket_template
            self.data.photobooth._p_changed = True
            transaction.commit()
        except (ConflictError, urllib2.HTTPError) as e:
            # Log and do nothing, we can wait for next update
            logger.exception(e)
            transaction.abort()

    def get_images_from_ticket_template(self, ticket_template):
        items = []
        if ticket_template:
            for image_variable in ticket_template['image_variables']:
                items.append(image_variable['items'])
            items.append(ticket_template['images'])
            items = [item for sub_items in items for item in sub_items]
            items = map(lambda x: x['image'], items)
            return items
        return items

    @transaction_decorate(retry_delay=1)
    def set_place(self, place):
        self.data.photobooth.place = place

    @transaction_decorate(retry_delay=1)
    def set_event(self, event):
        self.data.photobooth.event = event

    def update_photobooth(self):
        try:
            photobooth = figure.Photobooth.get(settings.RESIN_UUID)
            if photobooth:
                # check if place has changed
                place = photobooth.get('place')
                place_is_the_same = (place and self.data.photobooth.place and
                                     place['id'] == self.data.photobooth.place['id'])
                if not place_is_the_same:
                    self.set_place(place)
                # check if event has changed
                event = photobooth.get('event')
                event_is_the_same = (event and self.data.photobooth.event and
                                     event['id'] == self.data.photobooth.event['id'])
                if not event_is_the_same:
                    self.set_event(event)
                # check if ticket_template has changed
                ticket_template = photobooth['ticket_template']
                is_null = not self.data.photobooth.ticket_template
                has_been_modified = self.data.photobooth.ticket_template and \
                                    ticket_template['modified'] > self.data.photobooth.ticket_template['modified']
                if is_null or has_been_modified:
                    self.set_ticket_template(ticket_template)
        except figure.FigureError as e:
            # Log and do nothing, we can wait for next update
            logger.exception(e)


    @transaction_decorate(retry_delay=0.1)
    @timeit
    def get_code(self):
        # claim a code
        code = self.data.photobooth.codes.pop()
        self.data.photobooth._p_changed = True
        return code

    @transaction_decorate(retry_delay=5)
    def add_codes(self, codes):
        self.data.photobooth.codes.extend(codes)
        self.data.photobooth._p_changed = True

    def claim_new_codes_if_necessary(self):
        """ Claim new codes from api if there are less than 1000 codes left """
        if len(self.data.photobooth.codes) < 1000:
            try:
                new_codes = figure.CodeList.claim()['codes']
                self.add_codes(new_codes)
            except Exception as e:
                logger.exception(e)

    def upload_portraits(self):
        while self.data.photobooth.portraits:
            portrait = self.data.photobooth.portraits[0]
            try:
                api.create_portrait(portrait)
                self.pop_portrait()
            except figure.BadRequestError:
                # Duplicate code or files empty
                self.pop_portrait()
            except IOError as e:
                logger.exception(e)
                if e.errno == errno.ENOENT:
                    # snapshot or ticket file may be corrupted, proceed with remaining tickets
                    self.pop_portrait()
                else:
                    break
            except Exception as e:
                logger.exception(e)
                break

    @transaction_decorate(3)
    def pop_portrait(self):
        portrait = self.data.photobooth.portraits.pop(0)
        self.data.photobooth._p_changed = True
        return portrait

    @transaction_decorate(0.5)
    def add_portrait(self, portrait):
        self.data.photobooth.portraits.append(portrait)
        self.data.photobooth._p_changed = True

    def get_new_paper_level(self, pixels):
        if pixels == 0:
            # we are out of paper
            new_paper_level = 0
        else:
            old_paper_level = self.get_paper_level()
            if old_paper_level == 0:
                # Someone just refill the paper
                new_paper_level = 100
            else:
                cm = pixels2cm(pixels)
                new_paper_level = old_paper_level - (cm / float(settings.PAPER_ROLL_LENGTH)) * 100
                if new_paper_level <= 0:
                    # estimate is wrong, guess it's 10%
                    new_paper_level = 10
        self.set_paper_level(new_paper_level)
        return new_paper_level


    @transaction_decorate(0.5)
    def set_paper_level(self, paper_level):
        self.data.photobooth.paper_level = paper_level
        self.data.photobooth._p_changed = True

    def get_paper_level(self):
        return self.data.photobooth.paper_level

    def pack(self):
        self.storage.pack(wait=True)
        os.remove(os.path.join(settings.DATA_ROOT, 'db.fs.old'))


class Data(persistent.Persistent):
    """ OO data storage """

    def __init__(self):
        self.photobooth = Photobooth()
        self.version = DATABASE_VERSION


class Photobooth(persistent.Persistent):

    def __init__(self):
        self.ticket_template = None
        self.place = None
        self.event = None
        self.paper_level = 100
        self.codes = []
        self.portraits = []
