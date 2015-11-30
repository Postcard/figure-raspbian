# -*- coding: utf8 -*-

import pytest
import urllib2
from dateutil import parser
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

from figureraspbian import ticketpicker, ticketrenderer, utils, settings, api
from figureraspbian.db import Database, transaction_decorate, Installation
from figureraspbian.utils import timeit
from figureraspbian.app import App


@pytest.fixture
def mock_installation(request):
    return {
        "id": 1,
        "scenario": {
            "id": 1,
            "modified": "2015-01-01T00:00:00Z",
            "name": "15 ans",
            "objective": "Les quinze ans de Citadium",
            "ticket_templates": [
                {
                    "id": 1,
                    "modified": "2015-01-01T00:00:00Z",
                    "html": "<div class=\"figure figure-ticket-content\">\n  <div class=\"figure figure-placeholder\"><img class=\"figure figure-image\" id=\"872\" src=\"{{image_872}}\"></div>\n  <div class=\"figure figure-snapshot-container\">\n    <img class=\"figure figure-snapshot\" src=\"{{snapshot}}\">\n  </div>\n  <div class=\"figure figure-layer-container\"><img class=\"figure figure-image\" id=\"872\" src=\"{{image_872}}\"></div>\n  <div class=\"figure figure-footer-container\">\n    <p class=\"figure figure-static-footer\" style=\"text-align: center;\">\n      <span class=\"figure figure-generic-variable h1\" style=\"letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; display: inline-block; margin-top:10px;\" id=\"code\">{{code}}</span>\n      <br> Votre photo avec ce code\n      <br> sur jaiunticket.com\n    </p>\n  </div>\n</div>",
                    "text_variables": [],
                    "image_variables": [],
                    "images": [
                        {
                            "id": 1,
                            "image": "http://image.png",
                            "variable": None
                        }
                    ],
                    "probability": None
                }
            ]
        }
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

    def test_weighted_choice(self):
        """
        weighted choice should pick randomly in a list with weight
        """

        choices = [("choice1", 0.5), ("choice2", 0.5)]
        choice = utils.weighted_choice(choices)
        assert choice in [k for (k, v) in choices]

    def test_weighted_choices_only_one_choice(self):
        choices = [("onlychoice", 3)]
        choice = utils.weighted_choice(choices)
        assert choice == "onlychoice"

    def test_weighted_choice_weight_0(self):
        choices = [("choice1", 0.5), ("choice2", 0)]
        choice = utils.weighted_choice(choices)
        assert choice == "choice1"

    def test_weighted_choice_respect_statistics(self):
        choices = [("choice1", 0.3), ("choice2", 0.7)]
        occurrences = {"choice1": 0, "choice2": 0}
        for i in range(1, 10000):
            choice = utils.weighted_choice(choices)
            occurrences[choice] += 1
        assert 2500 < occurrences["choice1"] < 3500
        assert 6500 < occurrences["choice2"] < 7500

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
        filename = utils.get_file_name(1, datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p'))
        assert filename == 'Figure_mecojdary5j9resi.jpg'


class TestTicketPicker:

    def test_weighted_choice(self):
        """
        test_weighted_choice should pick a template based on his probability
        """
        choices = [
            {'id': '1', 'probability': 0.6},
            {'id': '2', 'probability': 0.2},
            {'id': '3', 'probability': 0.2}
        ]
        occurrences = {'1': 0, '2': 0, '3': 0}
        for i in range(1, 10000):
            choice = ticketpicker.weighted_choice(choices)
            occurrences[choice['id']] += 1
        assert 5500 < occurrences['1'] < 6500
        assert 1500 < occurrences['2'] < 2500
        assert 1500 < occurrences['3'] < 2500

    def test_weighted_choice_no_probabilty_provided(self):
        """
        test_weighted_choice should work when no probability are provided
        """
        choices = [
            {'id': '1', 'probability': None},
            {'id': '2', 'probability': None}
        ]
        occurrences = {'1': 0, '2': 0}
        for i in range(1, 10000):
            choice = ticketpicker.weighted_choice(choices)
            occurrences[choice['id']] += 1
        assert 4500 < occurrences['1'] < 5500
        assert 4500 < occurrences['2'] < 5500

    def test_weighted_choice_sum_probability_gte_1(self):
        """
        test_weighted_choice should work when no probability are provided
        """
        choices = [
            {'id': '1', 'probability': 0.9},
            {'id': '2', 'probability': 0.3}
        ]
        with pytest.raises(AssertionError):
            ticketpicker.weighted_choice(choices)


class TestTicketRenderer:

    def test_random_selection(self):
        """
        random selection should randomly select variable items
        """
        items = ['item1', 'item2', 'item3']
        variable = {'id': '1', 'items': ['item1', 'item2', 'item3']}
        id, item = ticketrenderer.random_selection(variable)
        assert id == '1'
        assert item in items

    def test_random_selection_empty_variable(self):
        """
        random selection should not throw if no items in variable
        """
        variable = {'id': '1', 'items': []}
        _, item = ticketrenderer.random_selection(variable)
        assert not item

    def test_render(self):
        """
        TicketRenderer should render a ticket when no random_snapshot
        """
        html = '{{snapshot}} {{code}} {{datetime | datetimeformat}} {{image_1}}'
        code = '5KIJ7'
        date = parser.parse("Tue Jun 22 07:46:22 EST 2010")
        images = [{'id': '1', 'image': 'path/to/image'}]
        rendered_html = ticketrenderer.render(
            html,
            'base64_encoded_snapshot',
            code,
            date,
            images)
        expected = 'base64_encoded_snapshot 5KIJ7 2010-06-22 ' \
                   'file:///Users/benoit/git/figure-raspbian/media/images/image'
        assert expected in rendered_html

    def test_set_date_format(self):
        """
        Ticket renderer should handle datetimeformat filter
        """
        html = '{{datetime | datetimeformat("%Y")}}'
        date = parser.parse("Tue Jun 22 07:46:22 EST 2010")
        rendered_html = ticketrenderer.render(html, '/path/to/snapshot', '00000', date, [])
        assert "2010" in rendered_html

    def test_encode_non_unicode_character(self):
        """
        Ticket renderer should encode non unicode character
        """
        html = u"Du texte avec un accent ici: é"
        date = parser.parse("Tue Jun 22 07:46:22 EST 2010")
        rendered_html = ticketrenderer.render(html, '/path/to/snapshot', '00000', date, [])
        assert u'Du texte avec un accent ici: é' in rendered_html

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

    def test_pixels2cm(self):
        """
        pixels2cm should convert image pixels into how many cm will actually be printed on the ticket
        """
        cm = utils.pixels2cm(1098)
        assert abs(cm - 14.5) < 0.1


class TestApi:

    def test_create_ticket(self, mocker):

        ticket = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': "2015-01-01T00:00:00Z",
            'code': 'JHUYG',
            'filename': 'Figure.jpg',
            'is_door_open': False
            }
        response = create_autospec(Response)
        response.status_code = 201
        response.text = json.dumps(ticket)
        session_post_mock = mocker.patch.object(Session, 'post', autospec=True)
        session_post_mock.return_value = response

        r = api.create_ticket(ticket)
        assert r == ticket
        assert session_post_mock.called

    def test_create_ticket_raise_Request_Exception(self, mocker):
        """
        create_ticket should propagate requests errors (ConectionError, HttpError, Timeout, etc)
        """

        ticket = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': "2015-01-01T00:00:00Z",
            'code': 'JHUYG',
            'filename': 'Figure.jpg',
            'is_door_open': False
            }
        session_post_mock = mocker.patch.object(Session, 'post', autospec=True)
        session_post_mock.side_effect = ConnectionError()

        with pytest.raises(ConnectionError):
            api.create_ticket(ticket)

    def test_create_ticket_raise_status_code_exception(self, mocker):
        """
        create_ticket should propagate erros caused by response.raise_for_status
        """
        ticket = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': "2015-01-01T00:00:00Z",
            'code': 'JHUYG',
            'filename': 'Figure.jpg',
            'is_door_open': False
            }
        response = create_autospec(Response)
        response.raise_for_status.side_effect = HTTPError()
        session_post_mock = mocker.patch.object(Session, 'post', autospec=True)
        session_post_mock.return_value = response

        with pytest.raises(HTTPError):
            api.create_ticket(ticket)


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

    def test_set_installation(self, mocker, db, mock_installation):
        """
        Installation should be updated correctly
        """
        api_download_mock = mocker.patch('figureraspbian.db.api.download', autospec=True)
        db.set_installation(mock_installation, datetime.now())
        installation = db.data.installation
        assert installation.id == 1
        assert installation.ticket_templates is not None
        api_download_mock.assert_called_once_with("http://image.png", os.path.join(settings.MEDIA_ROOT, 'images'))
        # check it only download images if necessary
        db.set_installation(mock_installation, datetime.now())
        api_download_mock.call_count == 1

    def test_set_installation_download_raise_exception(self, mocker, db, mock_installation):
        """
        Installation should not be initialized if download raise exception
        """
        api_download_mock = mocker.patch('figureraspbian.db.api.download', autospec=True)
        api_download_mock.side_effect = urllib2.HTTPError('', '', '', '', None)
        mock_transaction = mocker.patch('figureraspbian.db.transaction', autospec=True)
        db.set_installation(mock_installation, datetime.now())
        assert mock_transaction.abort.called
        assert not db.data.installation.id

    def test_update_installation(self, mocker, db, mock_installation):
        """
        update_installation should set installation the first time
        """
        set_installation_mock = mocker.patch.object(Database, 'set_installation', autospec=True)
        api_get_installation_mock = mocker.patch('figureraspbian.db.api.get_installation', autospec=True)
        api_get_installation_mock.return_value = mock_installation
        db.update_installation()
        api_get_installation_mock.call_count == 1
        args, kwargs = set_installation_mock.call_args
        assert mock_installation in args
        assert kwargs['modified'] == datetime(2015, 1, 1, 0, 0)

    def test_update_installation_new_id(self, mocker, db, mock_installation):
        """
        installation should be updated if id changes
        """
        db.data.installation.id = mock_installation['id']
        db.data.installation.ticket_templates = mock_installation['scenario']['ticket_templates']
        db.data.installation.modified = datetime(2015, 1, 1, 0, 0)
        mock_installation['id'] = 2
        api_get_installation_mock = mocker.patch('figureraspbian.db.api.get_installation', autospec=True)
        api_get_installation_mock.return_value = mock_installation
        set_installation_mock = mocker.patch.object(Database, 'set_installation', autospec=True)
        db.update_installation()
        args, kwargs = set_installation_mock.call_args
        assert mock_installation in args
        assert kwargs['modified'] == datetime(2015, 1, 1, 0, 0)

    def test_update_installation_not_modified(self, mocker, db, mock_installation):
        """
        update_installation should not update installation if it was not modified
        """
        db.data.installation.id = mock_installation['id']
        db.data.installation.ticket_templates = mock_installation['scenario']['ticket_templates']
        db.data.installation.modified = datetime(2015, 1, 1, 0, 0)
        api_get_installation_mock = mocker.patch('figureraspbian.db.api.get_installation', autospec=True)
        api_get_installation_mock.return_value = mock_installation
        set_installation_mock = mocker.patch.object(Database, 'set_installation', autospec=True)
        db.update_installation()
        assert not set_installation_mock.called

    def test_update_installation_modified(self, mocker, db, mock_installation):
        """
        update_installation should update installation
        """
        db.data.installation.id = mock_installation['id']
        db.data.installation.ticket_templates = mock_installation['scenario']['ticket_templates']
        db.data.installation.modified = datetime(2015, 1, 1, 0, 0)

        set_installation_mock = mocker.patch.object(Database, 'set_installation', autospec=True)

        api_get_installation_mock = mocker.patch('figureraspbian.db.api.get_installation', autospec=True)
        mock_installation['scenario']['modified'] = "2015-01-02T00:00:00Z"
        api_get_installation_mock.return_value = mock_installation
        db.update_installation()
        assert set_installation_mock.call_count == 1

        mock_installation['scenario']['ticket_templates'][0]['modified'] = "2015-01-03T00:00:00Z"
        api_get_installation_mock.return_value = mock_installation
        db.update_installation()
        assert set_installation_mock.call_count == 2

        mock_installation['scenario']['ticket_templates'] \
            .append(mock_installation['scenario']['ticket_templates'][0])
        api_get_installation_mock.return_value = mock_installation
        db.update_installation()
        assert set_installation_mock.call_count == 3


    def test_get_installation_return_none(self, mocker, db):
        """
        Installation should not be initialized if api return None
        """
        api_get_installation_mock = mocker.patch('figureraspbian.db.api.get_installation', autospec=True)
        api_get_installation_mock.return_value = None
        db.update_installation()
        set_installation_mock = mocker.patch.object(Database, 'set_installation', autospec=True)
        assert not set_installation_mock.called

    def test_get_installation_raise_exception(self, mocker, db):
        """
        Installation should not be initialized if get_installation raise Exception
        """
        api_get_installation_mock = mocker.patch('figureraspbian.db.api.get_installation', autospec=True)
        api_get_installation_mock.side_effect = HTTPError()
        set_installation_mock = mocker.patch.object(Database, 'set_installation', autospec=True)
        db.update_installation()
        assert not set_installation_mock.called

    def test_claim_codes_if_necessary(self, mocker, db):
        """
        it should claim new codes from the api if less than 1000 codes left
        """
        db.data.codes = ["AAAAA"] * 999
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
        db.data.codes = ["AAAAA"] * 1001
        claim_codes_mock = mocker.patch('figureraspbian.db.api.claim_codes', autospec=True)
        mocker.patch.object(Database, 'add_codes', autospec=True)
        db.claim_new_codes_if_necessary()
        assert not claim_codes_mock.called

    def test_get_code(self, db):
        """
        db.get_code should get a code and remove it from code list
        """
        db.data.codes = ['00000', '00001']
        code = db.get_code()
        assert code == '00001'
        assert db.data.codes == ['00000']

    def test_add_ticket(self, db):
        """
        db.add_ticket should add a ticket
        """
        assert len(db.data.tickets) == 0
        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        ticket = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': now,
            'code': 'JHUYG',
            }
        db.add_ticket(ticket)
        assert len(db.data.tickets) == 1

    def test_upload_tickets(self, mocker, db):
        """
        Uploading a ticket should upload all non uploaded tickets
        """
        api_create_ticket_mock = mocker.patch('figureraspbian.db.api.create_ticket', autospec=True)

        time1 = datetime.now(pytz.timezone(settings.TIMEZONE))
        time2 = datetime.now(pytz.timezone(settings.TIMEZONE))
        ticket_1 = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': time1,
            'code': 'JHUYG',
            'filename': 'Figure_foo.jpg'
        }
        ticket_2 = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': time2,
            'code': 'JU76G',
            'filename': 'Figure_bar.jpg'
        }
        db.add_ticket(ticket_1)
        db.add_ticket(ticket_2)
        db.upload_tickets()
        assert api_create_ticket_mock.call_count == 2
        assert db.data.tickets == []

    def test_upload_tickets_raise_error(self, mocker, db):
        """
        upload_tickets should stop while loop if it throws an error
        """
        api_create_ticket_mock = mocker.patch('figureraspbian.db.api.create_ticket', autospec=True)
        api_create_ticket_mock.side_effect = Exception()

        time1 = datetime.now(pytz.timezone(settings.TIMEZONE))
        time2 = datetime.now(pytz.timezone(settings.TIMEZONE))
        ticket_1 = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': time1,
            'code': 'JHUYG',
            'filename': 'Figure_foo.jpg'
        }
        ticket_2 = {
            'installation': '1',
            'snapshot': '/path/to/snapshot',
            'ticket': 'path/to/ticket',
            'dt': time2,
            'code': 'JU76G',
            'filename': 'Figure_bar.jpg'
        }
        db.add_ticket(ticket_1)
        db.add_ticket(ticket_2)
        db.upload_tickets()
        assert api_create_ticket_mock.call_count == 1
        assert len(db.data.tickets) == 2

    def test_add_printed_paper_length(self, mocker, db):
        """
        it should add a ticket length to current paper roll length
        """
        db.data.printed_paper_length = 70
        mock_pixels_to_cm = mocker.patch('figureraspbian.db.pixels2cm')
        mock_pixels_to_cm.return_value = 20
        db.add_printed_paper_length(1086)
        mock_pixels_to_cm.assert_called_with(1086)
        assert db.data.printed_paper_length == 90

    def test_set_printed_paper_length(self, mocker, db):
        db.data.printed_paper_length = 70
        mock_pixels_to_cm = mocker.patch('figureraspbian.db.pixels2cm')
        mock_pixels_to_cm.return_value = 20
        db.set_printed_paper_length(1086)
        mock_pixels_to_cm.assert_called_with(1086)
        assert db.data.printed_paper_length == 20


class TestApp:

    def test_trigger(self, mocker):
        """
        app.run() shoudl take a picture, print it and send data to the server
        """

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_ticket_mock = mocker.patch('figureraspbian.app.upload_ticket')
        upload_ticket_mock.delay.return_value = None

        set_paper_status_mock = mocker.patch('figureraspbian.app.set_paper_status')
        set_paper_status_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.return_value = None

        mock_installation = create_autospec(Installation)
        mock_installation.id = '1'
        mock_installation.modified = datetime(2015, 1, 1, 0, 0)
        mock_installation.ticket_templates = \
            [
                {
                    "id": 1,
                    "modified": "2015-01-01T00:00:00Z",
                    "html": "<div class=\"figure figure-ticket-content\">\n  <div class=\"figure figure-placeholder\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-snapshot-container\">\n    <img class=\"figure figure-snapshot\" src=\"{{snapshot}}\">\n  </div>\n  <div class=\"figure figure-layer-container\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-footer-container\">\n    <p class=\"figure figure-static-footer\" style=\"text-align: center;\">\n      <span class=\"figure figure-generic-variable h1\" style=\"letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; display: inline-block; margin-top:10px;\" id=\"code\">{{code}}</span>\n      <br> Votre photo avec ce code\n      <br> sur jaiunticket.com\n    </p>\n  </div>\n</div>",
                    "text_variables": [],
                    "image_variables": [],
                    "images": [
                        {
                            "id": 1,
                            "image": "http://image.png",
                            "variable": None
                        }
                    ],
                    "probability": None
                }
            ]
        mock_get_installation = mocker.patch.object(Database, 'get_installation', autospec=True)
        mock_get_installation.return_value = mock_installation

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        mock_add_printed_paper_length = mocker.patch.object(Database, 'add_printed_paper_length', autospec=True)
        mock_get_printed_paper_length = mocker.patch.object(Database, 'get_printed_paper_length', autospec=True)
        mock_get_printed_paper_length.return_value = 15

        input_mock.get_value.side_effect = [1, 0, -1]

        app = App(camera_mock, printer_mock, input_mock, output_mock)

        app.run()

        assert camera_mock.capture.call_count == 1
        assert printer_mock.print_ticket.call_count == 1
        assert upload_ticket_mock.delay.call_count == 1
        args1, _ = set_paper_status_mock.delay.call_args
        assert args1[0] == '1'
        assert args1[1] == 15
        args2, _ = mock_add_printed_paper_length.call_args
        assert args2[1] == 1086

    def test_first_trigger_after_paper_refill(self, mocker):
        """
        it should reset printed_paper_length
        """
        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_ticket_mock = mocker.patch('figureraspbian.app.upload_ticket')
        upload_ticket_mock.delay.return_value = None

        set_paper_status_mock = mocker.patch('figureraspbian.app.set_paper_status')
        set_paper_status_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.return_value = None

        mock_installation = create_autospec(Installation)
        mock_installation.id = '1'
        mock_installation.modified = datetime(2015, 1, 1, 0, 0)
        mock_installation.ticket_templates = \
            [
                {
                    "id": 1,
                    "modified": "2015-01-01T00:00:00Z",
                    "html": "<div class=\"figure figure-ticket-content\">\n  <div class=\"figure figure-placeholder\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-snapshot-container\">\n    <img class=\"figure figure-snapshot\" src=\"{{snapshot}}\">\n  </div>\n  <div class=\"figure figure-layer-container\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-footer-container\">\n    <p class=\"figure figure-static-footer\" style=\"text-align: center;\">\n      <span class=\"figure figure-generic-variable h1\" style=\"letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; display: inline-block; margin-top:10px;\" id=\"code\">{{code}}</span>\n      <br> Votre photo avec ce code\n      <br> sur jaiunticket.com\n    </p>\n  </div>\n</div>",
                    "text_variables": [],
                    "image_variables": [],
                    "images": [
                        {
                            "id": 1,
                            "image": "http://image.png",
                            "variable": None
                        }
                    ],
                    "probability": None
                }
            ]
        mock_get_installation = mocker.patch.object(Database, 'get_installation', autospec=True)
        mock_get_installation.return_value = mock_installation

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        mock_get_paper_status = mocker.patch.object(Database, 'get_paper_status', autospec=True)
        mock_get_paper_status.return_value = 0
        mock_set_paper_status = mocker.patch.object(Database, 'set_paper_status', autospec=True)

        mock_set_printed_paper_length = mocker.patch.object(Database, 'set_printed_paper_length', autospec=True)

        input_mock.get_value.side_effect = [1, 0, -1]

        app = App(camera_mock, printer_mock, input_mock, output_mock)

        app.run()

        args, _ = mock_set_printed_paper_length.call_args
        assert args[1] == 1086
        args, _ = mock_set_paper_status.call_args
        assert args[1] == 1

    def test_open_door(self, mocker):

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_ticket_mock = mocker.patch('figureraspbian.app.upload_ticket')
        upload_ticket_mock.delay.return_value = None

        set_paper_status_mock = mocker.patch('figureraspbian.app.set_paper_status')
        set_paper_status_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.return_value = None
        output_mock.turn_on.return_value = None
        output_mock.turn_off.return_value = None

        mock_installation = create_autospec(Installation)
        mock_installation.id = '1'
        mock_installation.modified = datetime(2015, 1, 1, 0, 0)
        mock_installation.ticket_templates = \
            [
                {
                    "id": 1,
                    "modified": "2015-01-01T00:00:00Z",
                    "html": "<div class=\"figure figure-ticket-content\">\n  <div class=\"figure figure-placeholder\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-snapshot-container\">\n    <img class=\"figure figure-snapshot\" src=\"{{snapshot}}\">\n  </div>\n  <div class=\"figure figure-layer-container\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-footer-container\">\n    <p class=\"figure figure-static-footer\" style=\"text-align: center;\">\n      <span class=\"figure figure-generic-variable h1\" style=\"letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; display: inline-block; margin-top:10px;\" id=\"code\">{{code}}</span>\n      <br> Votre photo avec ce code\n      <br> sur jaiunticket.com\n    </p>\n  </div>\n</div>",
                    "text_variables": [],
                    "image_variables": [],
                    "images": [
                        {
                            "id": 1,
                            "image": "http://image.png",
                            "variable": None
                        }
                    ],
                    "probability": None
                }
            ]
        mock_get_installation = mocker.patch.object(Database, 'get_installation', autospec=True)
        mock_get_installation.return_value = mock_installation

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
        assert upload_ticket_mock.delay.call_count == 1
        args, _ = upload_ticket_mock.delay.call_args
        ticket = args[0]
        assert ticket['is_door_open']

    def test_paper_empty(self, mocker):

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_ticket_mock = mocker.patch('figureraspbian.app.upload_ticket')
        upload_ticket_mock.delay.return_value = None

        set_paper_status_mock = mocker.patch('figureraspbian.app.set_paper_status')
        set_paper_status_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.side_effect = USBError("oups")
        output_mock.turn_on.return_value = None
        output_mock.turn_off.return_value = None

        mock_installation = create_autospec(Installation)
        mock_installation.id = '1'
        mock_installation.modified = datetime(2015, 1, 1, 0, 0)
        mock_installation.ticket_templates = \
            [
                {
                    "id": 1,
                    "modified": "2015-01-01T00:00:00Z",
                    "html": "<div class=\"figure figure-ticket-content\">\n  <div class=\"figure figure-placeholder\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-snapshot-container\">\n    <img class=\"figure figure-snapshot\" src=\"{{snapshot}}\">\n  </div>\n  <div class=\"figure figure-layer-container\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-footer-container\">\n    <p class=\"figure figure-static-footer\" style=\"text-align: center;\">\n      <span class=\"figure figure-generic-variable h1\" style=\"letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; display: inline-block; margin-top:10px;\" id=\"code\">{{code}}</span>\n      <br> Votre photo avec ce code\n      <br> sur jaiunticket.com\n    </p>\n  </div>\n</div>",
                    "text_variables": [],
                    "image_variables": [],
                    "images": [
                        {
                            "id": 1,
                            "image": "http://image.png",
                            "variable": None
                        }
                    ],
                    "probability": None
                }
            ]
        mock_get_installation = mocker.patch.object(Database, 'get_installation', autospec=True)
        mock_get_installation.return_value = mock_installation

        mock_get_code = mocker.patch.object(Database, 'get_code', autospec=True)
        mock_get_code.return_value = 'AAAAA'

        mock_claim_new_codes_if_necessary = mocker.patch.object(Database, 'claim_new_codes_if_necessary', autospec=True)
        mock_claim_new_codes_if_necessary.return_value = None

        mock_get_printed_paper_length = mocker.patch.object(Database, 'get_printed_paper_length', autospec=True)
        mock_get_printed_paper_length.return_value = 7900

        mock_set_paper_status_db = mocker.patch.object(Database, 'set_paper_status', autospec=True)

        input_mock.get_value.side_effect = [1, 0, -1]

        app = App(camera_mock, printer_mock, input_mock, output_mock)
        app.run()

        assert camera_mock.capture.call_count == 1
        assert printer_mock.print_ticket.call_count == 1
        assert upload_ticket_mock.delay.call_count == 1
        assert mock_get_printed_paper_length.call_count == 1
        args, _ = mock_set_paper_status_db.call_args
        assert args[1] == 0
        set_paper_status_mock.delay.assert_called_with('0', 7900)

    def test_open_door_paper_empty(self, mocker):

        camera_mock = Mock()
        printer_mock = Mock()
        input_mock = Mock()
        output_mock = Mock()

        upload_ticket_mock = mocker.patch('figureraspbian.app.upload_ticket')
        upload_ticket_mock.delay.return_value = None

        set_paper_status_mock = mocker.patch('figureraspbian.app.set_paper_status')
        set_paper_status_mock.delay.return_value = None

        camera_mock.capture.return_value = Image.open('test_snapshot.jpg')
        printer_mock.print_ticket.side_effect = USBError("oups")
        output_mock.turn_on.return_value = None
        output_mock.turn_off.return_value = None

        mock_installation = create_autospec(Installation)
        mock_installation.id = '1'
        mock_installation.modified = datetime(2015, 1, 1, 0, 0)
        mock_installation.ticket_templates = \
            [
                {
                    "id": 1,
                    "modified": "2015-01-01T00:00:00Z",
                    "html": "<div class=\"figure figure-ticket-content\">\n  <div class=\"figure figure-placeholder\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-snapshot-container\">\n    <img class=\"figure figure-snapshot\" src=\"{{snapshot}}\">\n  </div>\n  <div class=\"figure figure-layer-container\"><img class=\"figure figure-image\" id=\"1\" src=\"{{image_1}}\"></div>\n  <div class=\"figure figure-footer-container\">\n    <p class=\"figure figure-static-footer\" style=\"text-align: center;\">\n      <span class=\"figure figure-generic-variable h1\" style=\"letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; display: inline-block; margin-top:10px;\" id=\"code\">{{code}}</span>\n      <br> Votre photo avec ce code\n      <br> sur jaiunticket.com\n    </p>\n  </div>\n</div>",
                    "text_variables": [],
                    "image_variables": [],
                    "images": [
                        {
                            "id": 1,
                            "image": "http://image.png",
                            "variable": None
                        }
                    ],
                    "probability": None
                }
            ]
        mock_get_installation = mocker.patch.object(Database, 'get_installation', autospec=True)
        mock_get_installation.return_value = mock_installation

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
        assert upload_ticket_mock.delay.call_count == 1
        args, _ = upload_ticket_mock.delay.call_args
        ticket = args[0]
        assert ticket['is_door_open']




