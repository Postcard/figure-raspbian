
from peewee import *

from unittest import TestCase
from ..db import Database


class DatabaseTestCase(TestCase):

    def test_wrap_database(self):
        """ it should wrap an SQLiteDatabase and return a base model"""

        db = Database()
        db.connect_db()

        self.assertIsNotNone(db.database)
        self.assertIsNotNone(db.Model)

        class TestModel(db.Model):
            foo = CharField()

        db.database.create_tables([TestModel])

        tables = db.database.get_tables()
        self.assertEqual(len(tables), 1)

        db.close_db()


