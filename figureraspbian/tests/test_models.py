# -*- coding: utf8 -*-

from unittest import TestCase
import mock

from ..models import get_all_models, TicketTemplate, Text, Image, ImageVariable, TextVariable, Code, Photobooth
from ..models import Place, Event
from ..db import db
from .. import settings


class TextTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())

    def tearDown(self):
        db.close_db()

    def test_serialize(self):
        """ it should serialize object """
        data = {'id': 1, 'value': 'some text'}
        text = Text.create(**data)
        serialized = text.serialize()
        expected = {'id': 1, 'text': 'some text'}
        self.assertEqual(serialized, expected)

    def test_update_or_create_does_not_exist(self):
        """ it should create a new instance if the given text does not exist """
        data = {'id': 1, 'text': 'some text'}
        self.assertEqual(Text.select().count(), 0)
        Text.update_or_create(data, None)
        self.assertEqual(Text.select().count(), 1)
        text = Text.get(Text.id == 1)
        self.assertEqual(text.serialize(), data)

    def test_update_or_create_already_exists(self):
        """ it should update the fields of the already existing instance """
        data = {'id': 1, 'value': 'some text'}
        Text.create(**data)
        self.assertEqual(Text.select().count(), 1)
        data.pop('value')
        data['text'] = 'changed'
        Text.update_or_create(data, None)
        self.assertEqual(Text.select().count(), 1)
        text = Text.get(Text.id == 1)
        self.assertEqual(text.value, 'changed')


class ImageTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())

    def tearDown(self):
        db.close_db()

    def test_serialize(self):
        """ it should serialize image instance into dict """
        data = {'id': 1, 'path': '/path/to/image'}
        image = Image.create(**data)
        serialized = image.serialize()
        expected = {'id': 1, 'name': 'image'}
        self.assertEqual(serialized, expected)

    @mock.patch("figureraspbian.models.utils.download")
    def test_update_or_create_does_not_exists(self, mock_download):
        """ it should create an image if it does not exist and download the corresponding file """
        expected_path = '/path/to/image'
        mock_download.return_value = expected_path
        data = {'id': 1, 'image': 'https://url/to/image'}
        self.assertEqual(Image.select().count(), 0)
        Image.update_or_create(data)
        self.assertEqual(Image.select().count(), 1)
        mock_download.assert_called_with(data['image'], settings.IMAGE_ROOT)
        image = Image.get(Image.id == 1)
        self.assertEqual(image.path, expected_path)

    @mock.patch("figureraspbian.models.utils.download")
    def test_update_or_create_already_exist(self, mock_download):
        """ it should update image and download new image file """
        original_path = "/path/to/image1"
        Image.create(id=1, path=original_path)
        expected_path = "/path/to/image2"
        mock_download.return_value = expected_path
        self.assertEqual(Image.select().count(), 1)
        data = {'id': 1, 'image': 'https://url/to/image2', 'name': 'image2'}
        Image.update_or_create(data)
        mock_download.assert_called_with(data['image'], settings.IMAGE_ROOT)
        image = Image.get(Image.id == 1)
        self.assertEqual(image.path, expected_path)


class TextVariableTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())

    def tearDown(self):
        db.close_db()

    def test_serialize(self):
        """ it should serialize text variable instance into Python dict """
        data = {'id': 1, 'name': 'variable', 'mode': 'sequential'}
        text_variable = TextVariable.create(**data)
        serialized = text_variable.serialize()
        expected = {'items': [], 'mode': 'sequential', 'id': 1, 'name': 'variable'}
        self.assertEqual(serialized, expected)

    def test_update_or_create_does_not_exist(self):
        """ it should create a text variable if it does not exist """
        data = {'id': 1, 'name': 'variable', 'mode': 'sequential', 'items': []}
        self.assertEqual(TextVariable.select().count(), 0)
        TextVariable.update_or_create(data, None)
        self.assertEqual(TextVariable.select().count(),  1)

    def test_update_or_create_already_exists(self):
        """ it should update the fields of the already existing instance """
        data = {'id': 1, 'name': 'variable', 'mode': 'sequential', 'items': []}
        TextVariable.create(**data)
        self.assertEqual(TextVariable.select().count(),  1)
        data['name'] = 'changed'
        TextVariable.update_or_create(data, None)
        self.assertEqual(TextVariable.select().count(),  1)
        text = TextVariable.get(TextVariable.id == 1)
        self.assertEqual(text.name, 'changed')


class ImageVariableTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())

    def tearDown(self):
        db.close_db()

    def test_serialize(self):
        """ it should serialize an instance into Python dict """
        data = {'id': 1, 'name': 'variable', 'mode': 'sequential', 'items': []}
        image = ImageVariable.create(**data)
        serialized = image.serialize()
        expected = {'items': [], 'mode': 'sequential', 'id': 1, 'name': 'variable'}
        self.assertEqual(serialized, expected)

    def test_update_or_create_does_not_exist(self):
        """ it should create an image variable if it does not exist """
        data = {'id': 1, 'name': 'variable', 'mode': 'sequential', 'items': []}
        self.assertEqual(ImageVariable.select().count(), 0)
        ImageVariable.update_or_create(data, None)
        self.assertEqual(ImageVariable.select().count(), 1)

    def test_update_or_create_already_exist(self):
        """ it should update fields of an already existing instance """
        data = {'id': 1, 'name': 'variable', 'mode': 'sequential', 'items': []}
        ImageVariable.create(**data)
        self.assertEqual(ImageVariable.select().count(), 1)
        data['name'] = 'changed'
        ImageVariable.update_or_create(data)
        self.assertEqual(ImageVariable.select().count(), 1)
        image_variable = ImageVariable.get(id=1)
        image_variable.name = 'changed'


class TicketTemplateTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())

    def tearDown(self):
        db.close_db()

    def test_serialize(self):
        data = {'html': '<body></body>', 'modified': '2015-05-11T08:31:01Z', 'title': 'foo', 'description': 'bar', 'id': 1}
        ticket_template = TicketTemplate.create(**data)
        serialized = ticket_template.serialize()
        expected = {
            'description': 'bar',
            'title': 'foo',
            'modified': '2015-05-11T08:31:01Z',
            'image_variables': [],
            'html': '<body></body>',
            'images': [],
            'id': 1,
            'text_variables': []
        }
        self.assertEqual(serialized, expected)

    def test_update_or_create_does_not_exists(self):
        """ it should create a ticket template if it does not exist """
        data = {
            'id': 1,
            'html': '<body></body>',
            'modified': '2015-05-11T08:31:01Z',
            'title': 'foo',
            'description': 'bar',
            'text_variables': [],
            'images': [],
            'image_variables': []
        }
        self.assertEqual(TicketTemplate.select().count(), 0)
        TicketTemplate.update_or_create(data)
        self.assertEqual(TicketTemplate.select().count(), 1)
        ticket_template = TicketTemplate.get(TicketTemplate.id == 1)
        self.assertEqual(ticket_template.serialize(), data)

    def test_update_or_create__already_exists(self):
        """ it should update fields of the already existing instance """
        data = {
            'id': 1,
            'html': '<body></body>',
            'modified': '2015-05-11T08:31:01Z',
            'title': 'foo',
            'description': 'bar',
            'text_variables': [],
            'images': [],
            'image_variables': []
        }
        TicketTemplate.create(**data)
        self.assertEqual(TicketTemplate.select().count(), 1)
        data['title'] = 'changed'
        data['html'] = 'changed'
        data['description'] = 'changed'
        TicketTemplate.update_or_create(data)
        self.assertEqual(TicketTemplate.select().count(), 1)
        ticket_template = TicketTemplate.get(TicketTemplate.id == 1)
        self.assertEqual(ticket_template.serialize(), data)


class PhotoboothTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())
        self.uuid = "456d7e66247320147eda0a490df0c88a170f60f4378c7c1e3e77f845963c2e"
        Photobooth.get_or_create(uuid=self.uuid)

    def tearDown(self):
        db.close_db()

    @mock.patch("figureraspbian.models.utils.download")
    @mock.patch("figureraspbian.models.settings")
    def test_update_from_api_data(self, mock_settings, mock_download):
        """ it should update the photobooth """
        uuid = "456d7e66247320147eda0a490df0c88a170f60f4378c7c1e3e77f845963c2e"
        mock_settings.RESIN_UUID = uuid
        Photobooth.get_or_create(uuid=uuid)
        mock_download.return_value = '/path/to/image'
        photobooth = Photobooth.get()
        updated = {
            "id": 1,
            "serial_number": "FIG.00001",
            "place": {
                "id": 1,
                "name": "Atelier Commode",
                "tz": "Europe/Paris",
                "modified": "2017-03-18T15:20:01.711000Z",
                "code":"PPPP"
            },
            "event": {
                "id": 1,
                "name": "Attention à la mousse",
                "modified": "2016-09-01T08:29:21.705000Z",
                "code":"EEEE"
            },
            "ticket_template": {
                "id": 1,
                "modified": "2017-03-11T11:29:28Z",
                "html": "<!doctype html></html>",
                "title": "",
                "description": "",
                "text_variables": [],
                "image_variables": [],
                "images": []
            }
        }
        r = photobooth.update_from_api_data(updated)
        print(r)
        photobooth = Photobooth.get()
        self.assertEqual(Place.select().count(), 1)
        self.assertEqual(Event.select().count(), 1)
        self.assertEqual(TicketTemplate.select().count(), 1)
        self.assertEqual(photobooth.serial_number, "FIG.00001")
        self.assertEqual(photobooth.id, 1)
        self.assertEqual(photobooth.place.id, 1)
        self.assertEqual(photobooth.event.id, 1)
        self.assertEqual(photobooth.ticket_template.id, 1)


class CodeTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())

    def tearDown(self):
        db.close_db()

    def test_pop(self):
        """ it should pop a code from the available codes """
        codes = [
            {'value': 'CODE1'},
            {'value': 'CODE2'}
        ]
        for code in codes:
            Code.create(**code)
        self.assertEqual(Code.select().count(), 2)
        code = Code.pop()
        self.assertEqual(code, 'CODE1')
        self.assertEqual(Code.select().count(), 1)
        code = Code.pop()
        self.assertEqual(code, 'CODE2')
        self.assertEqual(Code.select().count(), 0)

    def test_bulk_insert(self):
        """ it should bulk insert an array of codes """

        codes = ["%05d" % n for n in range(0, 2000)]
        Code.bulk_insert(codes)
        self.assertEqual(Code.select().count(), len(codes))

    def test_less_than_1000_is_false(self):
        """ it should return true if we have less than 1000 codes left, false otherwise """
        codes = ["%05d" % n for n in range(0, 1000)]
        Code.bulk_insert(codes)
        self.assertFalse(Code.less_than_1000_left())
        Code.pop()
        self.assertTrue(Code.less_than_1000_left())
