# -*- coding: utf8 -*-

from peewee import Model, SqliteDatabase

from . import settings


class Database(object):
    def __init__(self, database=None):

        self.database = database

        if self.database is None:
            self.load_database()

        self.Model = self.get_model_class()

    def load_database(self):
        self.database = SqliteDatabase(settings.SQLITE_FILEPATH)

    def get_model_class(self):
        class BaseModel(Model):
            class Meta:
                database = self.database

        return BaseModel

    def connect_db(self):
        self.database.connect()

    def close_db(self):
        if not self.database.is_closed():
            self.database.close()


db = Database()
