# -*- coding: utf8 -*-

from contextlib import contextmanager
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import time
import os
import random

from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError
import transaction
import persistent
from requests.exceptions import Timeout, ConnectionError
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


class Database(object):

    def __init__(self):
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(storage)
        self.dbroot = self.db.open().root()
        if 'data' not in self.dbroot:
            self.dbroot['data'] = Data()
            transaction.commit()
        self.data = self.dbroot['data']

    def open(self):
        pass

    def close(self):
        self.db.close()

    def clear(self):
        self.dbroot['data'] = Data()
        transaction.commit()

    def update_installation(self):
        try:
            self.data.update_installation()
            transaction.commit()
        except (api.ApiException, Timeout, ConnectionError, ConflictError, urllib2.HTTPError) as e:
            logger.exception(e)
            transaction.abort()

    @transaction_decorate(retry_delay=0.1)
    def get_code(self):
        return self.data.installation.get_code()

    @transaction_decorate(retry_delay=0.1)
    def add_ticket(self, ticket):
        return self.data.add_ticket(ticket)

    def get_random_ticket(self):
        return self.data.get_random_ticket()

    def upload_tickets(self):
        while self.data.last_upload_index != (len(self.data.tickets) - 1):
            try:
                self.upload_oldest_ticket()
            except (Timeout, ConnectionError) as e:
                # We might have loose internet connection, break while loop
                logger.exception(e)
                break

    @transaction_decorate(retry_delay=5)
    def upload_oldest_ticket(self):
        self.data.upload_tickets()


class Data(persistent.Persistent):
    """
    This is a simple container for application data that can be stored at the root of the database
    """

    def __init__(self):
        self.installation = Installation()
        self.tickets = []
        self.last_upload_index = -1

    def add_ticket(self, ticket):
        self.tickets.append(ticket)
        self._p_changed = True

    def get_random_ticket(self):
        active_tickets = [ticket for ticket in self.tickets if ticket['installation'] == self.installation.id]
        return random.choice(active_tickets) if active_tickets else None

    def upload_tickets(self):
        """ Upload the older ticket """
        if len(self.tickets) > 0:
            ticket = self.tickets[self.last_upload_index + 1]
            try:
                api.create_ticket(ticket)
                self.last_upload_index += 1

            except api.ApiException as e:
                # Api error, proceed with remaining tickets
                logger.exception(e)
                self.last_upload_index += 1
            except IOError as e:
                # snapshot or ticket may not exist, proceed with remaining tickets
                logger.exception(e)
                self.last_upload_index += 1

    def update_installation(self):
        self.installation.update()


IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, 'images')


class Installation(persistent.Persistent):

    def __init__(self):
        self.id = None
        self.codes = []
        self.start = None
        self.end = None
        self.scenario = None
        self.ticket_template = None

    def update(self):
        """ Update the installation from Figure API """
        installation = api.get_installation()
        if installation is not None:
            scenario = installation['scenario']
            ticket_template = scenario['ticket_template']
            # Download all images that have not been previously downloaded
            items = [image_variable['items'] for image_variable in ticket_template['image_variables']]
            items.append(ticket_template['images'])
            items = [item for sub_items in items for item in sub_items]
            items = map(lambda x: x['image'], items)
            if not self.ticket_template:
                local_items = []
            else:
                local_items = [image_variable['items'] for image_variable in self.ticket_template['image_variables']]
                local_items.append(self.ticket_template['images'])
            local_items = [item for sub_items in local_items for item in sub_items]
            local_items = map(lambda x: x['image'], local_items)
            images_to_download = list(set(items) - set(local_items))
            for image in images_to_download:
                api.download(image, IMAGE_DIR)
            is_new = self.id != installation['id']
            new_codes = api.get_codes(installation['id']) if is_new else None

            if new_codes:
                self.codes = new_codes
            self.start = installation['start']
            self.end = installation['end']
            self.id = installation['id']
            self.scenario = scenario
            self.ticket_template = ticket_template
            self._p_changed = True

    def get_code(self):
        # claim a code
        code = self.codes.pop()
        self._p_changed = True
        return code



