from contextlib import contextmanager
import logging
logging.basicConfig(level='INFO')

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

    def __init__(self, env):
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(storage)
        self.data = None
        self.env = env

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
                api.download('static/css/ticket.css', settings.RESOURCE_DIR)
                self.data[self.env] = {}
                self.data[self.env]['installation'] = installation
                self.data[self.env]['scenario'] = scenario
                transaction.commit()
        except api.ApiException as e:
            logging.error(e.message)

    def is_initialized(self):
        return self.env in self.data

    def check_initialized(func):
        def check(self):
            if self.is_initialized() is False:
                raise NotInitializedError("Db was not yet initialized")
            return func(self)
        return check

    @check_initialized
    def installation(self):
        return self.data[self.env]['installation']

    @check_initialized
    def scenario(self):
        return self.data[self.env]['scenario']

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

    def close(self):
        self.db.close()


