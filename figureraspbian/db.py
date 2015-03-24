from ZEO import ClientStorage
from ZODB import DB
import transaction
import persistent
from . import settings, utils, api


class NotInitializedError(Exception):
    """Trying to access a database that was """
    pass


class Database(persistent.Persistent):

    def __init__(self, env):
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        self.db = DB(storage)
        self.data = self.db.open().root()
        self.env = env
        # flush data if in development
        if env is 'development':
            self.data.clear()
        transaction.commit()

    def update(self):
        if utils.internet_on():
            try:
                installation = api.get_installation()
                scenario = api.get_scenario(installation['scenario_obj']['id'])
                ticket_template = scenario['ticket_template']
                for image in ticket_template['images_objects']:
                    api.download(image['media'], settings.IMAGE_DIR)
                for image_variable in ticket_template['image_variables_objects']:
                    for image in image_variable['items']:
                        api.download(image['media'], settings.IMAGE_DIR)
            except api.ApiException:
                #TODO log error
                pass
            self.data[self.env] = {}
            self.data[self.env]['installation'] = installation
            self.data[self.env]['scenario'] = scenario
            transaction.commit()
        else:
            #TODO log something
            pass

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


