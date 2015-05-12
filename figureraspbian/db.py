# -*- coding: utf8 -*-

from contextlib import contextmanager
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import time

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


def transaction_decorate(func):
    def func_wrapper(self, *args, **kwargs):
        while True:
            try:
                result = func(self, *args, **kwargs)
                transaction.commit()
            except ConflictError:
                # Conflict occurred; this process should abort,
                # wait for a little bit, then try again.
                transaction.abort()
                time.sleep(1)
            else:
                # No ConflictError exception raised, so break
                # out of the enclosing while loop.
                return result
    return func_wrapper


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

    @transaction_decorate
    def get_code(self):
        return self.data.installation.get_code()

    @transaction_decorate
    def add_ticket(self, ticket):
        return self.data.add_ticket(ticket)

    def upload_tickets(self):
        while self.data.last_upload_index != (len(self.data.tickets) - 1):
            try:
                self.upload_oldest_ticket()
            except (Timeout, ConnectionError) as e:
                # We might have loose internet connection, break while loop
                logger.exception(e)
                break

    @transaction_decorate
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

    def update_installation(self):
        self.installation.update()


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
            is_new = self.id != installation['id']
            self.start = installation['start']
            self.end = installation['end']
            self.id = installation['id']
            self.scenario = installation['scenario']
            self.ticket_template = self.scenario['ticket_template']
            for image in self.ticket_template['images']:
                api.download(image['image'], settings.IMAGE_DIR)
            for image_variable in self.ticket_template['image_variables']:
                for image in image_variable['items']:
                    api.download(image['image'], settings.IMAGE_DIR)
            ticket_css_url = "%s/%s" % (settings.API_HOST, 'static/css/ticket.css')
            if is_new:
                self.codes = api.get_codes(self.id)
                self._p_changed = True
            api.download(ticket_css_url, settings.RESOURCE_DIR)

    def get_code(self):
        # claim a code
        code = self.codes.pop()
        self._p_changed = True
        return code



