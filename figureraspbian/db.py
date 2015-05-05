# -*- coding: utf8 -*-

from contextlib import contextmanager
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import time

from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError
from BTrees.OOBTree import OOBTree
import transaction
import persistent
from requests.exceptions import Timeout, ConnectionError
import urllib2


from . import settings, api


class NotInitializedError(Exception):
    """Trying to access a database that was """
    pass


@contextmanager
def managed(database):
    database.open()
    yield database
    database.close()


class Database(object):

    def __init__(self):
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(storage)
        self.dbroot = None

    def open(self):
        self.dbroot = self.db.open().root()
        if 'installation' not in self.dbroot:
            installation = Installation()
            self.dbroot['installation'] = installation
            transaction.commit()
            installation.update()
        if 'tickets' not in self.dbroot:
            self.dbroot['tickets'] = TicketsGallery()
            transaction.commit()

    def close(self):
        self.db.close()


class Installation(persistent.Persistent):

    def __init__(self):
        self.id = None
        self.codes = None
        self.start = None
        self.end = None
        self.scenario = None
        self.ticket_template = None

    def update(self):
        """ Update the installation from Figure API """
        try:
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
                api.download(ticket_css_url, settings.RESOURCE_DIR)
            else:
                self.id = None
                self.codes = None
                self.start = None
                self.end = None
                self.scenario = None
                self.ticket_template = None
            transaction.commit()
        except (api.ApiException, Timeout, ConnectionError, ConflictError, urllib2.HTTPError) as e:
            logger.exception(e)
            transaction.abort()

    def get_code(self):
        # claim a code
        while True:
            try:
                code = self.codes.pop()
                self._p_changed = 1
                transaction.commit()
            except ConflictError:
                # Conflict occurred; this process should abort,
                # wait for a little bit, then try again.
                transaction.abort()
                time.sleep(1)
            else:
                # No ConflictError exception raised, so break
                # out of the enclosing while loop.
                return code


class TicketsGallery(persistent.Persistent):

    def __init__(self):
        self._tickets = OOBTree()

    def add_ticket(self, ticket):
        """
        Add a ticket to the gallery.
        """
        ticket['uploaded'] = False
        while 1:
            try:
                self._tickets[ticket['dt']] = ticket
                self._p_changed = 1
                transaction.commit()
            except ConflictError:
                # Conflict occurred; this process should abort,
                # wait for a little bit, then try again.
                transaction.abort()
                time.sleep(1)
            else:
                # No ConflictError exception raised, so break
                # out of the enclosing while loop.
                break

    def upload_tickets(self):
        """
        Upload tickets
        """

        for dt, ticket in self._tickets.items():
            if not ticket['uploaded']:
                try:
                    # upload ticket
                    api.create_ticket(ticket)
                    while True:
                        try:
                            ticket['uploaded'] = True
                            self._tickets[dt] = ticket
                            self._p_changed = 1
                            transaction.commit()
                        except ConflictError:
                            # Conflict occurred; this process should abort,
                            # wait for a little bit, then try again.
                            transaction.abort()
                            time.sleep(1)
                        else:
                            # No ConflictError exception raised, so break
                            # out of the enclosing while loop.
                            break
                except api.ApiException as e:
                    # Api error, proceed with remaining tickets
                    logger.exception(e)
                    ticket['uploaded'] = True
                    self._tickets[dt] = ticket
                    self._p_changed = 1
                    transaction.commit()
                except (Timeout, ConnectionError) as e:
                    # We might have loose internet connection, break for loop
                    logger.exception(e)
                    break





