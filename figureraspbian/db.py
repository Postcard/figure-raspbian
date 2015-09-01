# -*- coding: utf8 -*-

from contextlib import contextmanager
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import time
import os
import random
import errno

from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError
import transaction
import persistent
from requests.exceptions import RequestException
import urllib2


from . import settings, api

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
DATABASE_VERSION = 2


class Database(object):
    """ Handle retrieving and updating data"""

    def __init__(self):
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(storage)
        self.dbroot = self.db.open().root()
        if 'data' not in self.dbroot:
            self.dbroot['data'] = Data()
            transaction.commit()
        # If local database is outdated, create a brand new one
        if not hasattr(self.dbroot['data'], 'version') or self.dbroot['data'].version < DATABASE_VERSION:
            self.dbroot['data'] = Data()
            transaction.commit()
        self.data = self.dbroot['data']

    def open(self):
        pass

    def close(self):
        self.db.close()

    @transaction_decorate(5)
    def clear(self):
        self.dbroot['data'] = Data()

    def get_installation(self):
        return self.data.installation

    def set_installation(self, installation):
        try:
            ticket_template = installation['scenario']['ticket_template']
            # Download all images that have not been previously downloaded
            items = [image_variable['items'] for image_variable in ticket_template['image_variables']]
            items.append(ticket_template['images'])
            items = [item for sub_items in items for item in sub_items]
            items = map(lambda x: x['image'], items)
            if not self.data.installation.ticket_template:
                local_items = []
            else:
                local_items = [image_variable['items'] for
                               image_variable in
                               self.data.installation.ticket_template['image_variables']]
                local_items.append(self.data.installation.ticket_template['images'])
            local_items = [item for sub_items in local_items for item in sub_items]
            local_items = map(lambda x: x['image'], local_items)
            images_to_download = list(set(items) - set(local_items))
            for image in images_to_download:
                api.download(image, IMAGE_DIR)
            self.data.installation.id = installation['id']
            self.data.installation.ticket_template = ticket_template
            self.data.installation._p_changed = True
            transaction.commit()
        except (ConflictError, urllib2.HTTPError) as e:
            # Log and do nothing, we can wait for next update
            logger.exception(e)
            transaction.abort()

    def update_installation(self):
        try:
            installation = api.get_installation()
            if installation:
                self.set_installation(installation)
        except (api.ApiException, RequestException) as e:
            # Log and do nothing, we can wait for next update
            logger.exception(e)

    @transaction_decorate(retry_delay=0.1)
    def get_code(self):
        # claim a code
        code = self.data.codes.pop()
        self.data._p_changed = True
        return code

    @transaction_decorate(retry_delay=5)
    def add_codes(self, codes):
        self.data.codes.extend(codes)
        self.data._p_changed = True

    def claim_new_codes_if_necessary(self):
        """ Claim new codes from api if there are less than 1000 codes left """
        if len(self.data.codes) < 1000:
            try:
                new_codes = api.claim_codes()
                self.add_codes(new_codes)
            except (api.ApiException, RequestException, urllib2.HTTPError) as e:
                logger.exception(e)

    def upload_tickets(self):
        while self.data.last_upload_index != (len(self.data.tickets) - 1):
            try:
                self.upload_oldest_ticket()
            except RequestException as e:
                # We might have loose internet connection, break while loop
                logger.exception(e)
                break

    def upload_oldest_ticket(self):
        """Upload the oldest ticket that has not been uploaded """
        if len(self.data.codes) > 0:
            last_upload_index = self.data.last_upload_index
            oldest_ticket = self.data.tickets[last_upload_index + 1]
            try:
                api.create_ticket(oldest_ticket)
                self.increment_last_upload_index()
            except api.ApiException as e:
                # Api error, proceed with remaining tickets
                logger.exception(e)
                self.increment_last_upload_index()
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise e
                # snapshot or ticket may not exist, proceed with remaining tickets
                logger.exception(e)
                self.increment_last_upload_index()


    @transaction_decorate(0.5)
    def add_ticket(self, ticket):
        self.data.tickets.append(ticket)
        self.data._p_changed = True

    def get_random_ticket(self):
        """ Returns a randomly selected ticket """
        active_tickets = [ticket for ticket in self.data.tickets if ticket['installation'] == self.data.installation.id]
        return random.choice(active_tickets) if active_tickets else None

    @transaction_decorate(1)
    def increment_last_upload_index(self):
        self.data.last_upload_index += 1
        self.data._p_changed = True


class Data(persistent.Persistent):
    """ OO data storage """

    def __init__(self):
        self.installation = Installation()
        self.codes = []
        self.tickets = []
        self.last_upload_index = -1
        self.version = DATABASE_VERSION


class Installation(persistent.Persistent):

    def __init__(self):
        self.id = None
        self.ticket_template = None



