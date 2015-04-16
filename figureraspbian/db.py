# -*- coding: utf8 -*-

from contextlib import contextmanager
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
import traceback

from ZEO import ClientStorage
from ZODB import DB
import transaction
import persistent

from . import settings, api


class NotInitializedError(Exception):
    """Trying to access a database that was """
    pass


@contextmanager
def managed(database):
    database.open()
    yield database
    database.close()


class Database(persistent.Persistent):

    def __init__(self):
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(storage)
        self.data = None

    def open(self):
        self.data = self.db.open().root()

    def clear(self):
        self.data.clear()
        transaction.commit()

    def update(self):
        try:
            installation = api.get_installation()
            if installation is not None:
                scenario = api.get_scenario(installation['scenario_obj']['id'])
                ticket_template = scenario['ticket_template']
                for image in ticket_template['images_objects']:
                    api.download(image['media'], settings.IMAGE_DIR)
                for image_variable in ticket_template['image_variables_objects']:
                    for image in image_variable['items']:
                        api.download(image['media'], settings.IMAGE_DIR)
                ticket_css_url = "%s/%s" % (settings.API_HOST, 'static/css/ticket.css')
                api.download(ticket_css_url, settings.RESOURCE_DIR)
                self.data['installation'] = installation
                self.data['scenario'] = scenario
                transaction.commit()
        except Exception:
            logger.error(traceback.format_exc())

    def is_initialized(self):
        return 'installation' in self.data

    def check_initialized(func):
        def check(self):
            if self.is_initialized() is False:
                raise NotInitializedError("Db was not yet initialized")
            return func(self)
        return check

    @check_initialized
    def installation(self):
        return self.data['installation']

    @check_initialized
    def scenario(self):
        return self.data['scenario']

    @check_initialized
    def ticket_template(self):
        return self.scenario()['ticket_template']

    @check_initialized
    def text_variables(self):
        return self.ticket_template()['text_variables_objects']

    @check_initialized
    def image_variables(self):
        return self.ticket_template()['image_variables_objects']

    @check_initialized
    def images(self):
        return self.ticket_template()['images_objects']

    def add_ticket(self, ticket):
        if 'tickets' in self.data:
            self.data['tickets'].append(ticket)
        else:
            self.data['tickets'] = [ticket]
        transaction.commit()

    def close(self):
        self.db.close()


