# -*- coding: utf8 -*-

import pytest
import urllib2
from datetime import datetime
import pytz
import time
import json
from usb.core import USBError


from mock import Mock, patch, create_autospec
import os
from ZODB.POSException import ConflictError
import transaction
from PIL import Image
from requests import Response, Session, ConnectionError, HTTPError

from figureraspbian import utils, settings, api
from figureraspbian.db import Database, transaction_decorate, Photobooth
from figureraspbian.utils import timeit
from figureraspbian.app import App


@pytest.fixture
def mock_ticket_template(request):

    return {
        "id": 1,
        "modified": "2015-01-01T00:00:00Z",
        "html": "<div></div>",
        "title": "title",
        "subtitle": "subtitle",
        "text_variables": [
            {
                "id": 1,
                "name": "sentiment",
                "items": ["Un peu", "Beaucoup"]
            }
        ],
        "image_variables": [
            {
                "id": "2",
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

@pytest.fixture
def mock_photobooth(request):

    return {
        "id": 1,
        "place": {
            "id": 1
        },
        "event": {
            "id": 1
        },
        "ticket_template": mock_ticket_template(request)
    }

@pytest.fixture
def mock_codes(request):
    return ['25JHU', '54KJI', 'KJ589', 'KJ78I', 'JIKO5']

@pytest.fixture
def db(request):
    # factory will only be invoked once per session -
    db = Database()
    def fin():
        db.clear()
        db.close()
    request.addfinalizer(fin)  # destroy when session is finished
    return db


class TestUtilityFunction:

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
        im = Image.open('test_ticket.jpg')
        mock_image_open = mocker.patch.object(Image, 'open')
        mock_image_open.return_value = im
        ticket_path, length = utils.get_pure_black_and_white_ticket('')
        assert ticket_path == '/Users/benoit/git/figure-raspbian/media/ticket.png'
        assert length == 958


class TestApi:

    def test_create_portrait(self, mocker):

        portrait = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': "2015-01-01T00:00:00Z",
            'place': None,
            'event': None,
            'code': "JHUYG",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }

        response = create_autospec(Response)
        response.status_code = 201
        response.text = json.dumps(portrait)
        session_post_mock = mocker.patch.object(Session, 'post', autospec=True)
        session_post_mock.return_value = response

        r = api.create_portrait(portrait)
        assert r == portrait
        assert session_post_mock.called

    def test_create_portrait_raise_Request_Exception(self, mocker):
        """
        create_portrait should propagate requests errors (ConectionError, HttpError, Timeout, etc)
        """

        portrait = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': "2015-01-01T00:00:00Z",
            'place': None,
            'event': None,
            'code': "JHUYG",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        session_post_mock = mocker.patch.object(Session, 'post', autospec=True)
        session_post_mock.side_effect = ConnectionError()

        with pytest.raises(ConnectionError):
            api.create_portrait(portrait)

    def test_create_ticket_raise_status_code_exception(self, mocker):
        """
        create_portrait should propagate erros caused by response.raise_for_status
        """
        portrait = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': "2015-01-01T00:00:00Z",
            'place': None,
            'event': None,
            'code': "JHUYG",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        response = create_autospec(Response)
        response.raise_for_status.side_effect = HTTPError()
        session_post_mock = mocker.patch.object(Session, 'post', autospec=True)
        session_post_mock.return_value = response

        with pytest.raises(HTTPError):
            api.create_portrait(portrait)

class TestDatabase:

    def test_transaction_decorator(self, mocker):
        """
        Transaction decorator should try a database write until there is no ConflictError
        """
        mock_transaction = mocker.patch('figureraspbian.db.transaction', autospec=True)
        func = Mock(return_value=1)
        @transaction_decorate(retry_delay=0.1)
        def should_be_commited(self):
            func()
        mock_transaction.commit.side_effect = [ConflictError, ConflictError, transaction.commit]
        should_be_commited('self')
        assert func.call_count == 3

    def test_set_ticket_template(self, mocker, db, mock_ticket_template):
        """
        Ticket Template should be set correctly
        """
        api_download_mock = mocker.patch('figureraspbian.db.api.download', autospec=True)
        db.set_ticket_template(mock_ticket_template)
        assert db.data.photobooth.ticket_template == mock_ticket_template
        api_download_mock.call_count == 2
        api_download_mock.assert_any_call("http://image1.png", os.path.join(settings.MEDIA_ROOT, 'images'))
        api_download_mock.assert_any_call("http://image2.png", os.path.join(settings.MEDIA_ROOT, 'images'))
        # check it only download images if necessary
        db.set_ticket_template(mock_ticket_template)
        api_download_mock.call_count == 2

    def test_set_ticket_template_download_raise_exception(self, mocker, db, mock_ticket_template):
        """
        Ticket template should not be set if download raise exception
        """
        api_download_mock = mocker.patch('figureraspbian.db.api.download', autospec=True)
        api_download_mock.side_effect = urllib2.HTTPError('', '', '', '', None)
        mock_transaction = mocker.patch('figureraspbian.db.transaction', autospec=True)
        db.set_ticket_template(mock_ticket_template)
        assert mock_transaction.abort.called
        assert not db.data.photobooth.ticket_template

    def test_update_photobooth(self, mocker, db, mock_photobooth):
        """
        update_photobooth should set place, event and ticket template the first time
        """
        set_ticket_template_mock = mocker.patch.object(Database, 'set_ticket_template', autospec=True)
        api_get_photobooth_mock = mocker.patch('figureraspbian.db.api.get_photobooth', autospec=True)
        api_get_photobooth_mock.return_value = mock_photobooth
        db.update_photobooth()
        api_get_photobooth_mock.call_count == 1
        args, kwargs = set_ticket_template_mock.call_args
        assert mock_photobooth['ticket_template'] in args
        assert db.data.photobooth.place == 1
        assert db.data.photobooth.event == 1

    def test_update_photobooth_no_place_no_event(self, mocker, db, mock_photobooth):
        db.data.photobooth.place = 1
        db.data.photobooth.event = 1
        mocker.patch.object(Database, 'set_ticket_template', autospec=True)
        api_get_photobooth_mock = mocker.patch('figureraspbian.db.api.get_photobooth', autospec=True)
        photobooth = mock_photobooth
        photobooth['place'] = None
        photobooth['event'] = None
        api_get_photobooth_mock.return_value = photobooth
        db.update_photobooth()
        assert db.data.photobooth.place == None
        assert db.data.photobooth.event == None

    def test_update_photobooth_ticket_template_not_modified(self, mocker, db, mock_photobooth):
        """
        update_photobooth should not set ticket_template if it was not modified
        """
        db.data.photobooth.ticket_template = mock_photobooth['ticket_template']
        api_get_photobooth_mock = mocker.patch('figureraspbian.db.api.get_photobooth', autospec=True)
        api_get_photobooth_mock.return_value = mock_photobooth
        set_ticket_template_mock = mocker.patch.object(Database, 'set_ticket_template', autospec=True)
        db.update_photobooth()
        assert not set_ticket_template_mock.called

    def test_update_photobooth_modified(self, mocker, db, mock_photobooth):
        """
        update_photobooth should set ticket template if it has been modified
        """
        import copy
        db.data.photobooth.ticket_template = copy.deepcopy(mock_photobooth['ticket_template'])
        api_get_photobooth_mock = mocker.patch('figureraspbian.db.api.get_photobooth', autospec=True)
        mock_photobooth['ticket_template']['modified'] = "2015-01-02T00:00:00Z"
        api_get_photobooth_mock.return_value = mock_photobooth
        set_ticket_template_mock = mocker.patch.object(Database, 'set_ticket_template', autospec=True)
        db.update_photobooth()
        assert set_ticket_template_mock.call_count == 1


    def test_get_photobooth_raise_exception(self, mocker, db):
        """
        Photobooth should catch exception and do nothing if api raises exception
        """
        api_get_photobooth_mock = mocker.patch('figureraspbian.db.api.get_photobooth', autospec=True)
        api_get_photobooth_mock.side_effect = HTTPError()
        db.update_photobooth()
        assert db.data.photobooth.ticket_template == None


    def test_claim_codes_if_necessary(self, mocker, db):
        """
        it should claim new codes from the api if less than 1000 codes left
        """
        db.data.photobooth.codes = ["AAAAA"] * 999
        claim_codes_mock = mocker.patch('figureraspbian.db.api.claim_codes', autospec=True)
        claim_codes_mock.return_value = ["BBBB"] * 1000
        mocker.patch.object(Database, 'add_codes', autospec=True)
        db.claim_new_codes_if_necessary()
        assert claim_codes_mock.called
        args, kwargs = db.add_codes.call_args
        assert ["BBBB"] * 1000 in args

    def test_do_not_claim_codes_if_not_necessary(self, mocker, db):
        """
        it should not claim new codes from the api if more than 1000 codes left
        """
        db.data.photobooth.codes = ["AAAAA"] * 1001
        claim_codes_mock = mocker.patch('figureraspbian.db.api.claim_codes', autospec=True)
        mocker.patch.object(Database, 'add_codes', autospec=True)
        db.claim_new_codes_if_necessary()
        assert not claim_codes_mock.called

    def test_get_code(self, db):
        """
        db.get_code should get a code and remove it from code list
        """
        db.data.photobooth.codes = ['00000', '00001']
        code = db.get_code()
        assert code == '00001'
        assert db.data.photobooth.codes == ['00000']

    def test_add_portrait(self, db):
        """
        db.add_portrait should add a portrait in local cache
        """
        assert len(db.data.photobooth.portraits) == 0
        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        portrait = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "JHUYG",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        db.add_portrait(portrait)
        assert len(db.data.photobooth.portraits) == 1

    def test_upload_portraits(self, mocker, db):
        """
        upload_portraits should upload all non uploaded portrait
        """
        api_create_portrait_mock = mocker.patch('figureraspbian.db.api.create_portrait', autospec=True)

        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        portrait1 = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "TITIS",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        portrait2 = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "TOTOS",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }

        db.add_portrait(portrait1)
        db.add_portrait(portrait2)
        db.upload_portraits()
        assert api_create_portrait_mock.call_count == 2
        assert db.data.photobooth.portraits == []

    def test_upload_portraits_raise_error(self, mocker, db):
        """
        upload_portraits should stop while loop if it throws an error
        """
        api_create_portrait_mock = mocker.patch('figureraspbian.db.api.create_portrait', autospec=True)
        api_create_portrait_mock.side_effect = Exception()

        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        portrait1 = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "TITIS",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        portrait2 = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "TOTOS",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        db.add_portrait(portrait1)
        db.add_portrait(portrait2)
        db.upload_portraits()
        assert api_create_portrait_mock.call_count == 1
        assert len(db.data.photobooth.portraits) == 2


    def test_upload_portraits_raise_ConnectionError(self, mocker, db):
        """
        upload_tickets should stop while loop if it throws a ConnectionError
        """
        api_create_portrait_mock = mocker.patch('figureraspbian.db.api.create_portrait', autospec=True)
        api_create_portrait_mock.side_effect = ConnectionError()

        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        portrait1 = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "TITIS",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        portrait2 = {
            'picture': '/path/to/picture',
            'ticket': 'path/to/ticket',
            'taken': now,
            'place': None,
            'event': None,
            'code': "TOTOS",
            'filename': 'Figure.jpg',
            'is_door_open': False
        }
        db.add_portrait(portrait1)
        db.add_portrait(portrait2)
        db.upload_portraits()
        assert api_create_portrait_mock.call_count == 1
        assert len(db.data.photobooth.portraits) == 2

    def test_get_new_paper_level(self, mocker, db):
        """
        it should decrease level of paper after a successful print
        """
        db.data.photobooth.paper_level = 50.0
        mock_pixels_to_cm = mocker.patch('figureraspbian.db.pixels2cm')
        mock_pixels_to_cm.return_value = 20
        new_paper_level = db.get_new_paper_level(1086)
        mock_pixels_to_cm.assert_called_with(1086)
        assert new_paper_level == 49.75
        assert db.get_paper_level() == 49.75

    def test_get_new_paper_level_paper_empty(self, db):
        """
        it should force paper level to 0 if we no ticket were printed
        """
        db.data.photobooth.paper_level = 10.0
        new_paper_level = db.get_new_paper_level(0)
        assert new_paper_level == 0.0
        assert db.get_paper_level() == 0.0

    def test_get_new_paper_level_paper_was_empty(self, db):
        """
        it should set paper level to 100 after a paper refill
        """
        db.data.photobooth.paper_level = 0.0
        new_paper_level = db.get_new_paper_level(1084)
        assert new_paper_level == 100.0
        assert db.get_paper_level() == 100.0

    def test_get_new_paper_level_inconsistant_guess(self, mocker, db):
        """
        it should set paper level to 10 if we reached 0 and there is still paper
        """
        db.data.photobooth.paper_level = 0.10
        mock_pixels_to_cm = mocker.patch('figureraspbian.db.pixels2cm')
        mock_pixels_to_cm.return_value = 20
        new_paper_level = db.get_new_paper_level(1086)
        mock_pixels_to_cm.assert_called_with(1086)
        assert new_paper_level == 10.0
        assert db.get_paper_level() == 10.0

    def test_pack_db(self, db):
        """
        packing db should reduce the size of the db
        """
        # increase size of db
        for i in range(0, 1000):
            db.dbroot['counter'] = i
            transaction.commit()
        assert os.path.getsize(os.path.join(settings.DATA_ROOT, 'db.fs')) > 100000
        db.pack()
        assert os.path.getsize(os.path.join(settings.DATA_ROOT, 'db.fs')) < 1000


class TestApp:

    def test_trigger(self, mocker, mock_ticket_template):
        """
        app.run() should take a picture, print it and send data to the server
        """

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_portrait_mock = mocker.patch('figureraspbian.app.upload_portrait')
        upload_portrait_mock.delay.return_value = None

        set_paper_level_mock = mocker.patch('figureraspbian.app.set_paper_level')
        set_paper_level_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.return_value = None

        mock_photobooth = create_autospec(Photobooth)
        mock_photobooth.place = "1"
        mock_photobooth.event = "1"
        mock_photobooth.ticket_template = mock_ticket_template

        mock_get_photobooth = mocker.patch.object(Database, 'get_photobooth', autospec=True)
        mock_get_photobooth.return_value = mock_photobooth

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        mock_get_new_paper_level = mocker.patch.object(Database, 'get_new_paper_level', autospec=True)
        mock_get_new_paper_level.return_value = 50

        input_mock.get_value.side_effect = [1, 0, -1]

        app = App(camera_mock, printer_mock, input_mock, output_mock)

        app.run()

        assert camera_mock.capture.call_count == 1
        assert printer_mock.print_ticket.call_count == 1
        assert upload_portrait_mock.delay.call_count == 1
        args, _ = upload_portrait_mock.delay.call_args
        portrait = args[0]
        assert portrait['code'] == 'AAAAA'
        assert portrait['place'] == '1'
        assert portrait['event'] == '1'
        args1, _ = set_paper_level_mock.delay.call_args
        assert args1[0] == 50

    def test_open_door(self, mocker, mock_ticket_template):

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_portrait_mock = mocker.patch('figureraspbian.app.upload_portrait')
        upload_portrait_mock.delay.return_value = None

        set_paper_level_mock = mocker.patch('figureraspbian.app.set_paper_level')
        set_paper_level_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.return_value = None
        output_mock.turn_on.return_value = None
        output_mock.turn_off.return_value = None

        mock_photobooth = create_autospec(Photobooth)
        mock_photobooth.place = "1"
        mock_photobooth.event = "1"
        mock_photobooth.ticket_template = mock_ticket_template

        mock_get_photobooth = mocker.patch.object(Database, 'get_photobooth', autospec=True)
        mock_get_photobooth.return_value = mock_photobooth

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        n = int(17.0 / 0.05)
        input_sequence = [1] * n
        input_sequence.extend([0, -1])
        input_mock.get_value.side_effect = input_sequence

        app = App(camera_mock, printer_mock, input_mock, output_mock)

        app.run()

        assert output_mock.turn_on.call_count == 1
        assert output_mock.turn_off.call_count == 1
        assert camera_mock.capture.call_count == 1
        assert printer_mock.print_ticket.call_count == 1
        assert upload_portrait_mock.delay.call_count == 1
        args, _ = upload_portrait_mock.delay.call_args
        portrait = args[0]
        assert portrait['is_door_open']

    def test_paper_empty(self, mocker, mock_ticket_template):

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_portrait_mock = mocker.patch('figureraspbian.app.upload_portrait')
        upload_portrait_mock.delay.return_value = None

        set_paper_level_mock = mocker.patch('figureraspbian.app.set_paper_level')
        set_paper_level_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.side_effect = USBError("oups")
        output_mock.turn_on.return_value = None
        output_mock.turn_off.return_value = None

        mock_photobooth = create_autospec(Photobooth)
        mock_photobooth.place = "1"
        mock_photobooth.event = "1"
        mock_photobooth.ticket_template = mock_ticket_template

        mock_get_photobooth = mocker.patch.object(Database, 'get_photobooth', autospec=True)
        mock_get_photobooth.return_value = mock_photobooth

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        mock_get_new_paper_level = mocker.patch.object(Database, 'get_new_paper_level', autospec=True)
        mock_get_new_paper_level.return_value = 0

        input_mock.get_value.side_effect = [1, 0, -1]

        app = App(camera_mock, printer_mock, input_mock, output_mock)
        app.run()

        assert camera_mock.capture.call_count == 1
        assert printer_mock.print_ticket.call_count == 1
        args, _ = mock_get_new_paper_level.call_args
        assert args[1] == 0
        assert upload_portrait_mock.delay.call_count == 1


    def test_open_door_paper_empty(self, mocker, mock_ticket_template):

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_portrait_mock = mocker.patch('figureraspbian.app.upload_portrait')
        upload_portrait_mock.delay.return_value = None

        set_paper_level_mock = mocker.patch('figureraspbian.app.set_paper_level')
        set_paper_level_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.side_effect = USBError("oups")
        output_mock.turn_on.return_value = None
        output_mock.turn_off.return_value = None

        mock_photobooth = create_autospec(Photobooth)
        mock_photobooth.place = "1"
        mock_photobooth.event = "1"
        mock_photobooth.ticket_template = mock_ticket_template

        mock_get_photobooth = mocker.patch.object(Database, 'get_photobooth', autospec=True)
        mock_get_photobooth.return_value = mock_photobooth

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        n = int(17.0 / 0.05)
        input_sequence = [1] * n
        input_sequence.extend([0, -1])
        input_mock.get_value.side_effect = input_sequence

        app = App(camera_mock, printer_mock, input_mock, output_mock)

        app.run()

        assert output_mock.turn_on.call_count == 1
        assert output_mock.turn_off.call_count == 1
        assert camera_mock.capture.call_count == 1
        assert printer_mock.print_ticket.call_count == 1
        assert upload_portrait_mock.delay.call_count == 1
        args, _ = upload_portrait_mock.delay.call_args
        ticket = args[0]
        assert ticket['is_door_open']




