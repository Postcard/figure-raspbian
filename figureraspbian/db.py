import pykka
import pickle
from . import settings, api, utils


class Database(pykka.ThreadingActor):

    def __init__(self, data):
        super(Database, self).__init__()
        self.db = data

    def update(self, db):
        self.db = db
        self.backup()

    def backup(self):
        dbfile = open(settings.DB_FILE, 'wb')
        pickle.dump(self.db)
        dbfile.close()

    def installation(self):
        return self.db['installation']

    def scenario(self):
        return self.db['scenario']

    def ticket_template(self):
        return self.db['ticket_template']

    def text_variables(self):
        return self.db['text_variables']

    def image_variables(self):
        return self.db['image_variables']


if utils.internet_on():
    # fetch fresh data from API
    try:
        initial_data = api.get_data()
    except Exception as e:
        print(e)
else:
    # fetch data from disk
    try:
        dbfile = open(settings.DB_FILE, 'rb')
        initial_data = pickle.load(dbfile)
        dbfile.close()
    except Exception as e:
        print(e)


db_ref = Database.start(db=initial_data)
db_proxy = db_ref.proxy