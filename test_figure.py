# -*- coding: utf8 -*-

import pytest
import time
from threading import Lock, Event as ThreadEvent
import pytz
from datetime import datetime
from os.path import join

from mock import Mock, patch, create_autospec, call
from figure.error import BadRequestError, APIConnectionError
from PIL import Image as PILImage

from figureraspbian import utils, settings
from figureraspbian.utils import timeit, download
from figureraspbian.devices.button import Button, PiFaceDigitalButton, EventThread, HoldThread
from figureraspbian.db import Photobooth, TicketTemplate, Place, Event, Code, Portrait, Text, Image, TextVariable, ImageVariable
from figureraspbian import db
from figureraspbian.photobooth import update, upload_portrait, upload_portraits, trigger
from figureraspbian.decorators import execute_if_not_busy


class TestUtils:

    def test_url2name(self):
        """
        url2name should extract file name in url
        """
        name = utils.url2name('http://api.figuredevices.com/static/css/ticket.css')
        assert name == 'ticket.css'

    @patch('figureraspbian.utils.logger.info')
    def test_timeit(self, mock_info):
        """
        timeit should log time spend in a function
        """
        @timeit
        def sleep():
            time.sleep(0.5)
            return "wake up"
        r = sleep()
        assert r == "wake up"
        assert mock_info.called

    def testpng2pos(self):
        """
        png2pos should convert an image into pos data ready to be sent to the printer
        """
        pos_data = utils.png2pos('test_ticket.jpg')
        assert pos_data

    def test_get_filename(self):
        filename = utils.get_file_name("CODES")
        assert filename == 'Figure_N5rIARTnVC1ySp0.jpg'

    def test_pixels2cm(self):
        """
        pixels2cm should convert image pixels into how many cm will actually be printed on the ticket
        """
        cm = utils.pixels2cm(1098)
        assert abs(cm - 14.5) < 0.1

    def test_get_pure_black_and_white_ticket(self, mocker):
        """
        it should convert PIL Image to '1' and return the path and the ticket length
        """
        im = PILImage.open('test_ticket.jpg')
        mock_image_open = mocker.patch.object(PILImage, 'open')
        mock_image_open.return_value = im
        ticket_path, length = utils.get_pure_black_and_white_ticket('')
        assert ticket_path == '/Users/benoit/git/figure-raspbian/media/ticket.png'
        assert length == 958

    def test_execute_if_not_busy(self):
        """
        it should execute function only if the lock is released
        """
        lock = Lock()
        mock_trigger = Mock()

        @execute_if_not_busy(lock)
        def trigger():
            mock_trigger()

        trigger()
        assert mock_trigger.call_count == 1
        assert not lock.locked()

        lock.acquire()
        trigger()
        assert mock_trigger.call_count == 1

    def test_download(self, mocker):
        """ it should download file if not present in local file system and return file path """
        mock_exists = mocker.patch('figureraspbian.utils.exists')
        mock_exists.return_value = False

        mock_urllib = mocker.patch('figureraspbian.utils.urllib2')
        mock_response = Mock()
        mock_urllib.urlopen.return_value = mock_response

        mock_write_file = mocker.patch('figureraspbian.utils.write_file')

        path = download('https://figure-integration.s3.amazonaws.com/media/images/1467986947463.jpg', settings.IMAGE_ROOT)

        assert path == join(settings.IMAGE_ROOT, '1467986947463.jpg')
        assert mock_urllib.urlopen.called
        assert mock_response.read.called
        assert mock_write_file.called

    def test_download_file_already_exists(self, mocker):
        """ it should not download file if it already exists in the file system """
        mock_exists = mocker.patch('figureraspbian.utils.exists')
        mock_exists.return_value = True
        path = download('https://figure-integration.s3.amazonaws.com/media/images/1467986947463.jpg', settings.IMAGE_ROOT)
        assert path == join(settings.IMAGE_ROOT, '1467986947463.jpg')


@pytest.fixture
def db_fixture(request):
    db.erase()
    db.init()

    def fin():
        db.close()
    request.addfinalizer(fin)  # destroy when session is finished
    return db


class TestDatabase:

    def test_get_photobooth(self, db_fixture):
        """ it should return the photobooth corresponding to RESIN_UUID"""

        ticket_template = TicketTemplate.create(html='<html></html>', title='title', description='description', modified='2015-01-01T00:00:00Z')
        sentiment = TextVariable.create(id='1', name='sentiment', ticket_template=ticket_template, mode='random')
        Text.create(value="Un peu", variable=sentiment)
        Text.create(value="beaucoup", variable=sentiment)
        Text.create(value="à la folie", variable=sentiment)
        logo = ImageVariable.create(id='2', name='logo', ticket_template=ticket_template, mode='random')
        Image.create(path='/path/to/image1', variable=logo)
        Image.create(path='/path/to/image2', variable=logo)
        Image.create(path='/path/to/image3', ticket_template=ticket_template)
        place = Place.create(id='1', name='Somewhere', timezone='Europe/Paris',  modified='2015-01-01T00:00:00Z')
        event = Event.create(id='1', name='Party',  modified='2015-01-01T00:00:00Z')
        db.update_photobooth(uuid='resin_uuid', id=1, place=place, event=event, ticket_template=ticket_template,
                                       paper_level=100)

        photobooth = db.get_photobooth()
        assert photobooth.uuid == 'resin_uuid'
        assert photobooth.place.name == 'Somewhere'
        assert photobooth.event.name == 'Party'
        ticket_template = photobooth.ticket_template
        assert ticket_template.html == '<html></html>'
        assert ticket_template.title == 'title'
        assert ticket_template.description == 'description'
        assert len(ticket_template.text_variables) == 1
        assert ticket_template.text_variables[0].name == 'sentiment'
        assert len(ticket_template.text_variables[0].items) == 3
        assert len(ticket_template.image_variables) == 1
        assert ticket_template.image_variables[0].name == 'logo'
        assert len(ticket_template.image_variables[0].items) == 2
        assert len(ticket_template.images) == 1

    def test_ticket_template_serializer(self, db_fixture):
        ticket_template = TicketTemplate.create(id=1, html='<html></html>', title='title', description='description', modified='2015-01-01T00:00:00Z')
        sentiment = TextVariable.create(id='1', name='sentiment', ticket_template=ticket_template, mode='random')
        Text.create(value="Un peu", variable=sentiment)
        Text.create(value="beaucoup", variable=sentiment)
        Text.create(value="à la folie", variable=sentiment)
        logo = ImageVariable.create(id='2', name='logo', ticket_template=ticket_template, mode='random')
        Image.create(path='/path/to/image1', variable=logo)
        Image.create(path='/path/to/image2', variable=logo)
        Image.create(path='/path/to/image3', ticket_template=ticket_template)
        expected = {
            'description': 'description',
            'title': 'title',
            'image_variables': [
                {
                    'items': [
                        {'id': 1, 'name': u'image1'},
                        {'id': 2, 'name': u'image2'}
                    ],
                    'mode': u'random',
                    'id': 2,
                    'name': u'logo'
                }
            ],
            'modified': '2015-01-01T00:00:00Z',
            'html': '<html></html>',
            'images': [
                {'id': 3, 'name': u'image3'}
            ],
            'id': 1,
            'text_variables': [
                {
                    'items': [
                        {'text': u'Un peu', 'id': 1},
                        {'text': u'beaucoup', 'id': 2},
                        {'text': u'\xe0 la folie', 'id': 3}
                    ],
                    'mode': u'random',
                    'id': 1,
                    'name': u'sentiment'}
            ]
        }
        assert ticket_template.serialize() == expected


    def test_get_code(self, db_fixture):
        """ it should return a code and delete it from the database """
        codes = ['AAAAA', 'BBBBB', 'CCCCC', 'DDDDD']
        for code in codes:
            Code.create(value=code)
        code = db.get_code()
        assert code == 'AAAAA'
        assert Code.select() == ['BBBBB', 'CCCCC', 'DDDDD']

    def test_get_portraits_to_be_uploaded(self, db_fixture):
        """ it should return the list of portraits that have not been marked as uploaded"""
        data_source = [
            {
                'code': 'AAAAA',
                'taken': datetime.now(pytz.timezone(settings.DEFAULT_TIMEZONE)),
                'place_id': '1',
                'event_id': '1',
                'photobooth_id': '1',
                'ticket': '/path/to/ticket1',
                'picture': '/path/to/picture1',
                'uploaded': False
            },
            {
                'code': 'BBBBB',
                'taken': datetime.now(pytz.timezone(settings.DEFAULT_TIMEZONE)),
                'place_id': '1',
                'event_id': '1',
                'photobooth_id': '1',
                'ticket': '/path/to/ticket2',
                'picture': '/path/to/picture2',
                'uploaded': True
            }
        ]

        for data_dict in data_source:
            Portrait.create(**data_dict)

        portraits_to_be_uploaded = db.get_portraits_to_be_uploaded()
        assert len(portraits_to_be_uploaded) == 1
        assert portraits_to_be_uploaded[0].code == 'AAAAA'

    def test_get_portrait_to_be_uploaded(self, db_fixture):
        """ it should return first portrait to be uploaded or None """
        data_source = [
            {
                'code': 'AAAAA',
                'taken': datetime.now(pytz.timezone(settings.DEFAULT_TIMEZONE)),
                'place_id': '1',
                'event_id': '1',
                'photobooth_id': '1',
                'ticket': '/path/to/ticket1',
                'picture': '/path/to/picture1',
                'uploaded': False
            },
            {
                'code': 'BBBBB',
                'taken': datetime.now(pytz.timezone(settings.DEFAULT_TIMEZONE)),
                'place_id': '1',
                'event_id': '1',
                'photobooth_id': '1',
                'ticket': '/path/to/ticket2',
                'picture': '/path/to/picture2',
                'uploaded': False
            }
        ]

        for data_dict in data_source:
            Portrait.create(**data_dict)

        p1 = db.get_portrait_to_be_uploaded()
        assert p1.code == 'AAAAA'
        assert p1.ticket == '/path/to/ticket1'
        assert p1.picture == '/path/to/picture1'
        p1.uploaded = True
        p1.save()
        p2 = db.get_portrait_to_be_uploaded()
        assert p2.code == 'BBBBB'
        assert p2.ticket == '/path/to/ticket2'
        assert p2.picture == '/path/to/picture2'
        p2.uploaded = True
        p2.save()
        assert not db.get_portrait_to_be_uploaded()

    def test_upload_portraits(self, db_fixture, mocker):

        data_source = [
            {
                'code': 'AAAAA',
                'taken': datetime.now(pytz.timezone(settings.DEFAULT_TIMEZONE)),
                'place_id': '1',
                'event_id': '1',
                'photobooth_id': '1',
                'ticket': '/path/to/ticket1',
                'picture': '/path/to/picture1',
                'uploaded': False
            },
            {
                'code': 'BBBBB',
                'taken': datetime.now(pytz.timezone(settings.DEFAULT_TIMEZONE)),
                'place_id': '1',
                'event_id': '1',
                'photobooth_id': '1',
                'ticket': '/path/to/ticket2',
                'picture': '/path/to/picture2',
                'uploaded': False
            }
        ]

        for data_dict in data_source:
            Portrait.create(**data_dict)

        mock_figure = mocker.patch('figureraspbian.photobooth.figure')
        mock_read_file = mocker.patch('figureraspbian.photobooth.read_file')
        upload_portraits()

        assert mock_read_file.call_args_list == [
            call(u'/path/to/picture1'),
            call(u'/path/to/ticket1'),
            call(u'/path/to/picture2'),
            call(u'/path/to/ticket2')]


    def test_update_or_create_text(self, db_fixture):
        """
        it should create or update a text instance
        """
        assert Text.select().count() == 0
        text = {'id': 1, 'text': 'some text'}
        db.update_or_create_text(text)
        instance = Text.get(Text.id == 1)
        assert Text.select().count() == 1
        assert instance.value == 'some text'
        text = {'id': 1, 'text': 'some longer text'}
        db.update_or_create_text(text)
        instance = Text.get(Text.id == 1)
        assert Text.select().count() == 1
        assert instance.value == 'some longer text'

    def test_update_or_create_text_variable(self, db_fixture):
        """
        it should update or create a text variable instance
        """
        assert TextVariable.select().count() == 0
        data = {
            "mode": "random",
            "id": 1,
            "name": "sentiment",
            "items": [{
                "id": 1,
                "text": "Un peu",
                "variable": 1
            }, {
                "id": 2,
                "text": "Beaucoup",
                "variable": 1
            }]
        }
        db.update_or_create_text_variable(data)
        assert TextVariable.select().count() == 1
        text_variable = TextVariable.get(TextVariable.id == 1)
        assert text_variable.name == 'sentiment'
        text_variable.items.count() == 2
        data['name'] = "towns"
        data['mode'] = "sequential"
        data['items'] = [{
            "id": 3,
            "text": "Paris",
            "variable": 1
        }, {
            "id": 4,
            "text": "Londres",
            "variable": 1
        }]
        Text.create(id=5, value='some other text')
        db.update_or_create_text_variable(data)
        text_variable = TextVariable.get(TextVariable.id == 1)
        assert text_variable.name == 'towns'
        assert text_variable.mode == 'sequential'
        assert text_variable.items.count() == 2
        items = text_variable.items
        assert len(items) == 2
        assert items[0].id == 3
        assert items[1].id == 4

    def test_update_or_create_image(self, mocker, db_fixture):
        """ it should update or create an image """
        assert Image.select().count() == 0
        data = {
            'id': 1,
            'image': 'https://path/to/image.jpg',
            'name': 'image.jpg'
        }
        download_mock = mocker.patch('figureraspbian.db.download')
        download_mock.return_value = '/path/to/image.jpg'
        db.update_or_create_image(data)
        image = Image.get(Image.id == 1)
        assert download_mock.call_count == 1
        assert image.path == '/path/to/image.jpg'
        db.update_or_create_image(data)
        assert download_mock.call_count == 1
        data = {
            'id': 1,
            'image': 'https://path/to/image2.jpg',
            'name': 'image2.jpg'
        }
        download_mock.return_value = '/path/to/image2.jpg'
        db.update_or_create_image(data)
        assert download_mock.call_count == 2
        image = Image.get(Image.id == 1)
        assert image.path == '/path/to/image2.jpg'

    def test_update_or_create_image_variable(self, mocker, db_fixture):
        assert ImageVariable.select().count() == 0
        data = {
            "mode": "random",
            "id": 1,
            "name": "landscape",
            "items": [
                {
                    "id": 1,
                    "image": "https://path/to/image.jpg",
                    "name": "image.jpg",
                }
            ]
        }
        download_mock = mocker.patch('figureraspbian.db.download')
        download_mock.return_value = '/path/to/image.jpg'
        db.update_or_create_image_variable(data)
        image_variable = ImageVariable.get(ImageVariable.id == 1)
        assert image_variable.name == 'landscape'
        assert len(image_variable.items) == 1
        assert download_mock.call_count == 1
        assert(image_variable.items[0].id == 1)
        data['mode'] = 'sequential'
        data['name'] = 'planets'
        data['items'] = [
            {
                "id": 2,
                "image": "https://path/to/image2.jpg",
                "name": "image2.jpg"
            }
        ]
        Image.create(id=3, path='/path/to/image3.jpg')
        db.update_or_create_image_variable(data)
        download_mock.return_value = '/path/to/image2.jpg'
        image_variable = ImageVariable.get(ImageVariable.id == 1)
        assert Image.select().count() == 2
        assert image_variable.mode == 'sequential'
        assert image_variable.name == 'planets'
        assert len(image_variable.items)
        assert image_variable.items[0].id == 2
        assert download_mock.call_count == 2

    def test_update_or_create_ticket_template(self, mocker, db_fixture):

        data = {
            "id": 1,
            "modified": "2015-01-01T00:00:00Z",
            "html": "<div></div>",
            "title": "title",
            "description": "description",
            "text_variables": [
                {
                    "mode": "random",
                    "id": 1,
                    "name": "sentiment",
                    "items": [{
                        "id": 1,
                        "text": "Un peu",
                        "variable": 1
                    }, {
                        "id": 2,
                        "text": "Beaucoup",
                        "variable": 1
                    }]
                }
            ],
            "image_variables": [
                {
                    "mode": "random",
                    "id": 2,
                    "name": "landscape",
                    "items": [
                        {
                            "id": 2,
                            "image": "http://image2.png",
                            "name": "image2",
                            "variable": 2
                        }
                    ]
                }
            ],
            "images": [{
                "id": 1,
                "image": "http://image1.png",
                "name": "image1.png",
                "variable": None
            }]
        }
        download_mock = mocker.patch('figureraspbian.db.download')
        download_mock.return_value = '/path/to/image.jpg'
        db.update_or_create_ticket_template(data)
        ticket_template = TicketTemplate.get(TicketTemplate.id == 1)
        assert ticket_template.html == '<div></div>'
        assert ticket_template.title == 'title'
        assert ticket_template.description == 'description'
        assert len(ticket_template.text_variables) == 1
        assert len(ticket_template.text_variables[0].items) == 2
        assert len(ticket_template.images) == 1
        assert len(ticket_template.image_variables) == 1
        assert len(ticket_template.image_variables[0].items) == 1
        data['modified'] = '2015-01-02T00:00:00Z'
        data['html'] = '<div>some text</div>'
        data['title'] = 'title2'
        data['description'] = 'description2'
        db.update_or_create_ticket_template(data)
        ticket_template = TicketTemplate.get(TicketTemplate.id == 1)
        assert ticket_template.modified == '2015-01-02T00:00:00Z'
        assert ticket_template.html == '<div>some text</div>'
        assert ticket_template.title == 'title2'
        assert ticket_template.description == 'description2'

    def test_update_photobooth(self, db_fixture):
        place = Place.create(name='somewhere', tz='Europe/Paris', modified='2015-01-02T00:00:00Z')
        event = Event.create(name='party', modified='2015-01-02T00:00:00Z')
        db.update_photobooth(place=place, event=event, id=2, counter=1)
        photobooth = db.get_photobooth()
        assert photobooth.counter == 1
        assert photobooth.place == place
        assert photobooth.event == event
        assert photobooth.id == 2

    def test_increment_counter(self, db_fixture):
        """
        it should increment the photobooth photo counter
        """
        photobooth = db.get_photobooth()
        assert photobooth.counter == 0
        db.increment_counter()
        photobooth = db.get_photobooth()
        assert photobooth.counter == 1

    def test_bulk_insert_codes(self, db_fixture):
        """
        it should create codes from an array of codes
        """
        codes = ['AAAAA'] * 1001
        db.bulk_insert_codes(codes)
        assert Code.select().count() == 1001

    def test_should_claim_codes(self, db_fixture):
        """
        it should return True if and only if number of codes is below 1000
        """
        codes = ['AAAAA'] * 1001
        db.bulk_insert_codes(codes)
        assert db.should_claim_code() == False
        db.get_code()
        db.get_code()
        assert db.should_claim_code() == True

    def test_delete_ticket_template(self, db_fixture):
        """
        it should not cascade deletion to Photobooth instance
        """
        tt = TicketTemplate.create(html='html', title='title', description='description', modified='2015-01-02T00:00:00Z')
        photobooth = db.get_photobooth()
        photobooth.ticket_template = tt
        photobooth.save()
        db.delete(photobooth.ticket_template)
        db.update_photobooth(ticket_template=None)
        photobooth = db.get_photobooth()
        assert photobooth is not None
        assert photobooth.ticket_template is None
        assert TicketTemplate.select().count() == 0

    def test_delete_place(self, db_fixture):
        """
        it should not cascade deletion to Photobooth instance
        """
        place = Place.create(name='Le Pop Up du Label', modified='2015-01-02T00:00:00Z')
        photobooth = db.get_photobooth()
        photobooth.place = place
        photobooth.save()
        db.delete(photobooth.place)
        db.update_photobooth(place=None)
        photobooth = db.get_photobooth()
        assert photobooth is not None
        assert photobooth.place is None
        assert Place.select().count() == 0

    def test_delete_event(self, db_fixture):
        """
        it should not cascade deletion to Photobooth instance
        """
        event = Event.create(name='La wedding #5', modified='2015-01-02T00:00:00Z')
        photobooth = db.get_photobooth()
        photobooth.event = event
        photobooth.save()
        db.delete(photobooth.event)
        db.update_photobooth(event=None)
        photobooth = db.get_photobooth()
        assert photobooth is not None
        assert photobooth.event is None
        assert Event.select().count() == 0

    def test_update_paper_level(self, db_fixture):
        pass


class TestPhotobooth:

    def test_update_on_the_first_time(self, mocker):
        """ it should create place, event and ticket template and associate it to the photobooth instance """
        mock_db = mocker.patch('figureraspbian.photobooth.db')
        mock_photobooth = create_autospec(Photobooth)
        mock_photobooth.place = None
        mock_photobooth.event = None
        mock_photobooth.ticket_template = None
        mock_db.get_photobooth.return_value = mock_photobooth

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Photobooth')
        mock_api.get.return_value = {
            'id': 2,
            'serial_number': 'FIG 00001',
            'uuid': settings.RESIN_UUID,
            'place': {
                'id': 1,
                'modified': '2016-06-07T07:50:41Z',
                'name': 'Le Pop up du Label',
                'tz': 'Europe/Paris',
            },
            'event': {
                'id': 1,
                'modified': '2016-06-07T07:50:41Z',
                'name': 'La wedding #5'
            },
            'ticket_template': {
                'id': 1,
                'modified': '2016-06-07T07:50:41Z',
                'html': 'html',
                'title': 'title',
                'description': 'description',
                'text_variables': [
                    {
                        'id': '1',
                        'mode': 'random',
                        'name': 'textvariable',
                        'items': [
                            {'id': '1', 'text': 'text'}
                        ]
                    }
                ],
                'image_variables': [
                    {
                        'id': '2',
                        'mode': 'random',
                        'name': 'imagevariable',
                        'items': [
                            {
                                'id': '1',
                                'image': 'image'
                            }
                        ]
                    }
                ],
                'images': [
                    {
                        'id': '2',
                        'image': 'image2'
                    }
                ]
            }
        }
        update()
        assert mock_db.create_place.called
        assert mock_db.create_event.called
        assert mock_db.update_or_create_ticket_template.called
        assert mock_db.update_photobooth.call_count == 4
        assert mock_db.update_photobooth.call_args_list[0] == call(id=2, serial_number='FIG 00001')



    def test_update_reset(self, mocker):
        """ it should delete place, event and ticket template and set corresponding value to None on photobooth """
        mock_db = mocker.patch('figureraspbian.photobooth.db')
        mock_photobooth = create_autospec(Photobooth)
        mock_place = create_autospec(Place)
        mock_event = create_autospec(Event)
        mock_ticket_template = create_autospec(TicketTemplate)
        mock_photobooth.place = mock_place
        mock_photobooth.event = mock_event
        mock_photobooth.ticket_template = mock_ticket_template
        mock_db.get_photobooth.return_value = mock_photobooth
        mock_api = mocker.patch('figureraspbian.photobooth.figure.Photobooth')
        mock_api.get.return_value = {
            'id': 2,
            'serial_number': 'FIG 00002',
            'uuid': settings.RESIN_UUID,
            'place': None,
            'event': None,
            'ticket_template': None
        }
        update()
        assert mock_db.delete.call_args_list == [call(mock_place), call(mock_event), call(mock_ticket_template)]
        assert mock_db.update_photobooth.call_args_list == [
            call(id=2, serial_number='FIG 00002'),
            call(place=None),
            call(event=None),
            call(ticket_template=None)]

    def test_different_id(self, mocker):
        """
        it should create new instances of place, event and ticket_template, associate it to the photobooth instance
        and delete previous instances of placce, event and ticket_template
        """
        mock_db = mocker.patch('figureraspbian.photobooth.db')
        mock_photobooth = create_autospec(Photobooth)
        mock_place = create_autospec(Place)
        mock_place.id = 1
        mock_event = create_autospec(Event)
        mock_event.id = 1
        mock_ticket_template = create_autospec(TicketTemplate)
        mock_ticket_template.id = 1
        mock_photobooth.place = mock_place
        mock_photobooth.event = mock_event
        mock_photobooth.ticket_template = mock_ticket_template
        mock_db.get_photobooth.return_value = mock_photobooth

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Photobooth')
        mock_api.get.return_value = {
            'id': 2,
            'uuid': settings.RESIN_UUID,
            'serial_number': 'FIG 00002',
            'place': {
                'id': 2,
            },
            'event': {
                'id': 2,
            },
            'ticket_template': {
                'id': 2,
            }
        }
        update()
        assert mock_db.delete.call_args_list == [call(mock_place), call(mock_event), call(mock_ticket_template)]
        assert mock_db.create_place.call_args_list == [call({'id': 2})]
        assert mock_db.create_event.call_args_list == [call({'id': 2})]
        assert mock_db.update_or_create_ticket_template.call_args_list == [call({'id': 2})]
        assert mock_db.update_photobooth.call_count == 4

    def test_same_id_but_modified(self, mocker):
        """
        it should update place, event, and ticket template
        """
        mock_db = mocker.patch('figureraspbian.photobooth.db')
        mock_photobooth = create_autospec(Photobooth)
        mock_place = create_autospec(Place)
        mock_place.id = 1
        mock_place.modified = '2016-06-01T00:00:00Z'
        mock_event = create_autospec(Event)
        mock_event.id = 1
        mock_event.modified = '2016-06-01T00:00:00Z'
        mock_ticket_template = create_autospec(TicketTemplate)
        mock_ticket_template.id = 1
        mock_ticket_template.modified = '2016-06-01T00:00:00Z'
        mock_photobooth.place = mock_place
        mock_photobooth.event = mock_event
        mock_photobooth.ticket_template = mock_ticket_template
        mock_db.get_photobooth.return_value = mock_photobooth

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Photobooth')
        mock_api.get.return_value = {
            'id': 1,
            'uuid': settings.RESIN_UUID,
            'place': {
                'id': 1,
                'modified': '2016-06-02T00:00:00Z'
            },
            'event': {
                'id': 1,
                'modified': '2016-06-02T00:00:00Z'
            },
            'ticket_template': {
                'id': 1,
                'modified': '2016-06-02T00:00:00Z'
            }
        }
        update()
        assert mock_db.update_place.callled
        assert mock_db.update_event.called
        assert mock_db.update_or_create_ticket_template.called

    def test_upload_portrait_raise_exception(self, mocker):
        """ it should save portrait to local db and filesystem if any error occurs during the upload"""
        mock_api = mocker.patch('figureraspbian.photobooth.figure.Portrait')
        mock_api.create.side_effect = Exception
        mock_db = mocker.patch('figureraspbian.photobooth.db')
        mock_write_file = mocker.patch('figureraspbian.photobooth.write_file')
        portrait = {
            'picture': 'base64encodedfile',
            'ticket': 'base64encodedfile',
            'taken': 'somedate',
            'place': '1',
            'event': '1',
            'photobooth': '1',
            'code': 'AAAAA',
            'filename': 'Figure_dqidqid.jpg'
        }
        upload_portrait(portrait)
        assert mock_write_file.call_args_list == [
            call('base64encodedfile', join(settings.PICTURE_ROOT,  'Figure_dqidqid.jpg')),
            call('base64encodedfile', join(settings.TICKET_ROOT,  'Figure_dqidqid.jpg'))]
        assert mock_db.create_portrait.call_args_list == [call({
            'picture': join(settings.PICTURE_ROOT,  'Figure_dqidqid.jpg'),
            'code': 'AAAAA',
            'place': '1',
            'photobooth': '1',
            'taken': 'somedate',
            'ticket': join(settings.TICKET_ROOT,  'Figure_dqidqid.jpg'),
            'event': '1'})]
        assert mock_api.create.call_args_list == [call(
            files={'ticket': ('Figure_dqidqid.jpg', 'base64encodedfile'), 'picture_color': ('Figure_dqidqid.jpg', 'base64encodedfile')},
            data={'taken': 'somedate', 'code': 'AAAAA', 'place': '1', 'event': '1', 'photobooth': '1'})]

    def test_upload_portraits(self, mocker):
        """ it should upload all non uploaded portraits and set uploaded to False"""
        mock_db = mocker.patch('figureraspbian.photobooth.db')
        portrait1 = create_autospec(Portrait)
        portrait2 = create_autospec(Portrait)
        portrait3 = create_autospec(Portrait)

        portrait1.id = 1
        portrait1.code = 'AAAAA'
        portrait1.taken = '2016-06-02T00:00:00Z'
        portrait1.place_id = '1'
        portrait1.event_id = '1'
        portrait1.photobooth_id = '1'
        portrait1.picture = '/path/to/picture'
        portrait1.ticket = '/path/to/ticket'
        portrait1.uploaded = False

        portrait2.id = 2
        portrait2.code = 'BBBBB'
        portrait2.taken = '2016-06-02T00:00:00Z'
        portrait2.place_id = '1'
        portrait2.event_id = '1'
        portrait2.photobooth_id = '1'
        portrait2.picture = '/path/to/picture'
        portrait2.ticket = '/path/to/ticket'
        portrait2.uploaded = False

        portrait3.id = 3
        portrait3.code = 'CCCCC'
        portrait3.taken = '2016-06-02T00:00:00Z'
        portrait3.place_id = '1'
        portrait3.event_id = '1'
        portrait3.photobooth_id = '1'
        portrait3.picture = '/path/to/picture'
        portrait3.ticket = '/path/to/ticket'
        portrait3.uploaded = False

        mock_db.get_portrait_to_be_uploaded.side_effect = [portrait1, portrait2, portrait3, None]

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Portrait')

        mock_read_file = mocker.patch('figureraspbian.photobooth.read_file')
        mock_read_file.return_value = 'file content'

        upload_portraits()

        assert mock_api.create.call_args_list == [
            call(files={'ticket': 'file content', 'picture_color': 'file content'},
                 data={'taken': '2016-06-02T00:00:00Z', 'code': 'AAAAA', 'place': '1', 'event': '1', 'photobooth': '1'}),
            call(files={'ticket': 'file content', 'picture_color': 'file content'},
                 data={'taken': '2016-06-02T00:00:00Z', 'code': 'BBBBB', 'place': '1', 'event': '1', 'photobooth': '1'}),
            call(files={'ticket': 'file content', 'picture_color': 'file content'},
                 data={'taken': '2016-06-02T00:00:00Z', 'code': 'CCCCC', 'place': '1', 'event': '1', 'photobooth': '1'})
        ]

        assert mock_db.update_portrait.call_args_list == [
            call(1, uploaded=True),
            call(2, uploaded=True),
            call(3, uploaded=True)
        ]

    def test_upload_portraits_raise_unknown_exception(self, mocker):

        mock_db = mocker.patch('figureraspbian.photobooth.db')
        portrait1 = create_autospec(Portrait)
        portrait2 = create_autospec(Portrait)
        portrait3 = create_autospec(Portrait)

        portrait1.id = 1
        portrait1.code = 'AAAAA'
        portrait1.taken = '2016-06-02T00:00:00Z'
        portrait1.place_id = '1'
        portrait1.event_id = '1'
        portrait1.photobooth_id = '1'
        portrait1.picture = '/path/to/picture'
        portrait1.ticket = '/path/to/ticket'
        portrait1.uploaded = False

        portrait2.id = 2
        portrait2.code = 'BBBBB'
        portrait2.taken = '2016-06-02T00:00:00Z'
        portrait2.place_id = '1'
        portrait2.event_id = '1'
        portrait2.photobooth_id = '1'
        portrait2.picture = '/path/to/picture'
        portrait2.ticket = '/path/to/ticket'
        portrait2.uploaded = False

        portrait3.id = 3
        portrait3.code = 'CCCCC'
        portrait3.taken = '2016-06-02T00:00:00Z'
        portrait3.place_id = '1'
        portrait3.event_id = '1'
        portrait3.photobooth_id = '1'
        portrait3.picture = '/path/to/picture'
        portrait3.ticket = '/path/to/ticket'
        portrait3.uploaded = False

        mock_db.get_portrait_to_be_uploaded.side_effect = [portrait1, portrait2, portrait3, None]

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Portrait')
        mock_api.create.side_effect = Exception

        mock_read_file = mocker.patch('figureraspbian.photobooth.read_file')
        mock_read_file.return_value = 'file content'

        upload_portraits()

        assert mock_db.get_portrait_to_be_uploaded.call_count == 1
        assert mock_api.create.call_count == 1
        assert mock_db.delete.call_count == 0

    def test_upload_portrait_raise_BadRequest(self, mocker):

        mock_db = mocker.patch('figureraspbian.photobooth.db')
        portrait1 = create_autospec(Portrait)
        portrait2 = create_autospec(Portrait)
        portrait3 = create_autospec(Portrait)

        portrait1.id = 1
        portrait1.code = 'AAAAA'
        portrait1.taken = '2016-06-02T00:00:00Z'
        portrait1.place_id = '1'
        portrait1.event_id = '1'
        portrait1.photobooth_id = '1'
        portrait1.picture = '/path/to/picture'
        portrait1.ticket = '/path/to/ticket'
        portrait1.uploaded = False

        portrait2.id = 2
        portrait2.code = 'BBBBB'
        portrait2.taken = '2016-06-02T00:00:00Z'
        portrait2.place_id = '1'
        portrait2.event_id = '1'
        portrait2.photobooth_id = '1'
        portrait2.picture = '/path/to/picture'
        portrait2.ticket = '/path/to/ticket'
        portrait2.uploaded = False

        portrait3.id = 3
        portrait3.code = 'CCCCC'
        portrait3.taken = '2016-06-02T00:00:00Z'
        portrait3.place_id = '1'
        portrait3.event_id = '1'
        portrait3.photobooth_id = '1'
        portrait3.picture = '/path/to/picture'
        portrait3.ticket = '/path/to/ticket'
        portrait3.uploaded = False

        mock_db.get_portrait_to_be_uploaded.side_effect = [portrait1, portrait2, portrait3, None]

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Portrait')
        mock_api.create.side_effect = BadRequestError

        mock_read_file = mocker.patch('figureraspbian.photobooth.read_file')
        mock_read_file.return_value = 'file content'

        upload_portraits()

        assert mock_db.get_portrait_to_be_uploaded.call_count == 4
        assert mock_api.create.call_count == 3
        assert mock_db.delete.call_count == 3

    def test_upload_portraits_raise_ConnectionError(self, mocker):

        mock_db = mocker.patch('figureraspbian.photobooth.db')
        portrait1 = create_autospec(Portrait)
        portrait2 = create_autospec(Portrait)
        portrait3 = create_autospec(Portrait)

        portrait1.id = 1
        portrait1.code = 'AAAAA'
        portrait1.taken = '2016-06-02T00:00:00Z'
        portrait1.place_id = '1'
        portrait1.event_id = '1'
        portrait1.photobooth_id = '1'
        portrait1.picture = '/path/to/picture'
        portrait1.ticket = '/path/to/ticket'
        portrait1.uploaded = False

        portrait2.id = 2
        portrait2.code = 'BBBBB'
        portrait2.taken = '2016-06-02T00:00:00Z'
        portrait2.place_id = '1'
        portrait2.event_id = '1'
        portrait2.photobooth_id = '1'
        portrait2.picture = '/path/to/picture'
        portrait2.ticket = '/path/to/ticket'
        portrait2.uploaded = False

        portrait3.id = 3
        portrait3.code = 'CCCCC'
        portrait3.taken = '2016-06-02T00:00:00Z'
        portrait3.place_id = '1'
        portrait3.event_id = '1'
        portrait3.photobooth_id = '1'
        portrait3.picture = '/path/to/picture'
        portrait3.ticket = '/path/to/ticket'
        portrait3.uploaded = False

        mock_db.get_portrait_to_be_uploaded.side_effect = [portrait1, portrait2, portrait3, None]

        mock_api = mocker.patch('figureraspbian.photobooth.figure.Portrait')
        mock_api.create.side_effect = APIConnectionError

        mock_read_file = mocker.patch('figureraspbian.photobooth.read_file')
        mock_read_file.return_value = 'file content'

        upload_portraits()

        assert mock_db.get_portrait_to_be_uploaded.call_count == 1
        assert mock_api.create.call_count == 1
        assert mock_db.delete.call_count == 0

    @pytest.mark.skip(reason="need an API server running on localhost")
    def test_upload_portrait_no_mock(self):

        picture = PILImage.open('test_snapshot.jpg')
        ticket = PILImage.open('test_ticket.jpg')

        import cStringIO
        buf1 = cStringIO.StringIO()
        picture.save(buf1, "JPEG")
        picture_io = buf1.getvalue()

        buf2 = cStringIO.StringIO()
        ticket.save(buf2, "JPEG")
        ticket_io = buf2.getvalue()

        portrait = {
            'picture': picture_io,
            'ticket': ticket_io,
            'taken': datetime.now(pytz.timezone('Europe/Paris')),
            'place': 1,
            'event': None,
            'photobooth': 1,
            'code': 'JUFD0',
            'filename': 'Figure_JHUGTTX.jpg'
        }

        upload_portrait(portrait)


    def test_trigger(self, mocker):
        """it should take a picture, print a ticket and send data to the server"""

        mock_camera = mocker.patch('figureraspbian.photobooth.camera')
        mock_camera.capture.return_value = PILImage.open('test_snapshot.jpg')
        mock_printer = mocker.patch('figureraspbian.photobooth.printer')

        mock_db = mocker.patch('figureraspbian.photobooth.db')

        mock_ticket_template = create_autospec(TicketTemplate)
        serialized = {
            'description': 'description',
            'title': 'title',
            'image_variables': [],
            'modified': '2015-01-01T00:00:00Z',
            'html': '<html></html>',
            'images': [],
            'id': 1,
            'text_variables': []
        }
        mock_ticket_template.serialize.return_value = serialized

        mock_place = create_autospec(Place)
        mock_place.tz = 'Europe/Paris'
        mock_place.id = 1

        mock_event = create_autospec(Event)
        mock_event.id = 1

        mock_photobooth = create_autospec(Photobooth)
        mock_photobooth.id = 1
        mock_photobooth.ticket_template = mock_ticket_template
        mock_photobooth.counter = 0
        mock_photobooth.place = mock_place
        mock_photobooth.event = mock_event

        mock_db.get_photobooth.return_value = mock_photobooth

        mock_db.get_code.return_value = 'AAAAA'

        mock_update_paper_level = mocker.patch('figureraspbian.photobooth.update_paper_level_async')
        mock_claim_new_codes = mocker.patch('figureraspbian.photobooth.claim_new_codes_async')
        mock_upload_portrait = mocker.patch('figureraspbian.photobooth.upload_portrait_async')

        trigger()

        assert mock_camera.capture.called
        assert mock_printer.print_ticket.called
        assert mock_update_paper_level.called
        assert mock_claim_new_codes.called
        assert mock_upload_portrait.called



class TestButtton:

    def test_register_when_pressed(self):
        """ it should register when_pressed callback"""
        mock_function = Mock()
        def when_pressed():
            mock_function()
        button = Button(1, 0.05, 2)
        button.when_pressed = when_pressed
        button._fire_activated()
        assert mock_function.called

    def test_register_when_held(self):
        """ it should register when_held callback """
        mock_function = Mock()
        def when_held():
            mock_function()
        button = Button(1, 0.05, 2)
        button.when_held = when_held
        button._fire_held()
        assert mock_function.called


class TestEventThread:

    def test_fire_events(self):
        """
        it set active and inactive events based on parent button value
        """
        mock_button = create_autospec(Button)
        mock_button._last_state = None
        mock_button._inactive_event = ThreadEvent()
        mock_button._active_event = ThreadEvent()
        mock_button._holding = ThreadEvent()

        event_thread = EventThread(mock_button)
        mock_button.value.return_value = 0
        event_thread._fire_events(mock_button)

        assert mock_button._inactive_event.is_set()

        mock_button.value.return_value = 1
        event_thread._fire_events(mock_button)

        assert mock_button._active_event.is_set()
        assert mock_button._fire_activated.called



class TestHoldThread:

    def test_hold(self):
        """ it should fire held callback if the button is held enough time"""

        mock_button = create_autospec(Button)
        mock_button.hold_time = 0.1
        mock_button._fire_held = Mock()
        mock_button._inactive_event = ThreadEvent()
        mock_button._holding = ThreadEvent()

        hold_thread = HoldThread(mock_button)
        mock_button._holding.set()
        hold_thread.start()
        time.sleep(0.2)
        mock_button._inactive_event.set()
        time.sleep(0.1)
        hold_thread.stop()
        assert mock_button._fire_held.called

    def test_not_hold(self):
        """ it should not fire heled callback if the button is not held enough time"""

        mock_button = create_autospec(PiFaceDigitalButton)
        mock_button.hold_time = 0.2
        mock_button._fire_held = Mock()
        mock_button._inactive_event = ThreadEvent()
        mock_button._holding = ThreadEvent()

        hold_thread = HoldThread(mock_button)
        mock_button._holding.set()
        hold_thread.start()
        time.sleep(0.1)
        mock_button._inactive_event.set()
        time.sleep(0.1)
        hold_thread.stop()
        assert not mock_button._fire_held.called






