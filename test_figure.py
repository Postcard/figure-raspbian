# -*- coding: utf8 -*-

import unittest
from copy import deepcopy
import urllib2
from dateutil import parser
from datetime import datetime
import pytz

from mock import MagicMock, Mock, call
import os
from ZEO import ClientStorage
from ZODB import DB
from ZODB.POSException import ConflictError
import transaction


from figureraspbian import ticketrenderer, utils, settings, api
from figureraspbian.db import Database, managed, transaction_decorate


class TestTicketRenderer(unittest.TestCase):

    def test_random_selection(self):
        """
        random selection should randomly select variable items
        """
        items = ['item1', 'item2', 'item3']
        variable = {'id': '1', 'items': ['item1', 'item2', 'item3']}
        id, item = ticketrenderer.random_selection(variable)
        self.assertEqual(id, '1')
        self.assertIn(item, items)

    def test_random_selection_empty_variable(self):
        """
        random selection should not throw if no items in variable
        """
        variable = {'id': '1', 'items': []}
        _, item = ticketrenderer.random_selection(variable)
        self.assertIsNone(item)

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
        self.assertIn(expected, rendered_html)

    def test_set_date_format(self):
        """
        Ticket renderer should handle datetimeformat filter
        """
        html = '{{datetime | datetimeformat("%Y")}}'
        date = parser.parse("Tue Jun 22 07:46:22 EST 2010")
        rendered_html = ticketrenderer.render(html, '/path/to/snapshot', '00000', date, [])
        self.assertIn("2010", rendered_html)

    def test_encode_non_unicode_character(self):
        """
        Ticket renderer should encode non unicode character
        """
        html = u"Du texte avec un accent ici: é"
        date = parser.parse("Tue Jun 22 07:46:22 EST 2010")
        rendered_html = ticketrenderer.render(html, '/path/to/snapshot', '00000', date, [])
        self.assertTrue(u'Du texte avec un accent ici: é' in rendered_html)


class TestUtilityFunction(unittest.TestCase):

    def test_url2name(self):
        """
        url2name should extract file name in url
        """
        name = utils.url2name('http://api.figuredevices.com/static/css/ticket.css')
        self.assertEqual(name, 'ticket.css')


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.mock_installation = {
            "scenario": {
                "name": "Marabouts",
                "modified": "2015-05-11T08:31:01Z",
                "ticket_templates": [{
                    "modified": "2015-05-11T08:31:01Z",
                    "html": "<html></html>",
                    "text_variables": [
                        {
                            "owner": "test@figuredevices.com",
                            "id": 1,
                            "name": "Profession",
                            "items": [
                                {
                                    "owner": "test@figuredevices.com",
                                    "id": 1,
                                    "text": "Professeur",
                                    "variable": 1
                                },
                                {
                                    "owner": "test@figuredevices.com",
                                    "id": 2,
                                    "text": "Monsieur",
                                    "variable": 1
                                }
                            ]
                        }
                    ],
                    "image_variables": [{
                        "owner": "test@figuredevices.com",
                        "id": 1,
                        "name": "Profession",
                        "items": [
                            {
                                "image": "http://image1"
                            },
                            {
                                "image": "http://image2"
                            }
                        ]
                    }],
                    "images": [
                        {"image": "http://image3"},
                        {"image": "http://image4"}]
                }]
            },
            "place": None,
            "start": "2016-07-01T12:00:00Z",
            "end": "2016-07-02T12:00:00Z",
            "id": "1"
        }
        self.mock_codes = ['25JHU', '54KJI', 'KJ589', 'KJ78I', 'JIKO5']
        with managed(Database()) as db:
            db.clear()

    def test_transaction_decorator(self):
        """
        Transaction decorator should try a database write until there is no ConflictError
        """
        storage = ClientStorage.ClientStorage(settings.ZEO_SOCKET)
        db = DB(storage)
        dbroot = db.open().root()
        m = Mock()
        m.side_effect = [ConflictError, transaction.commit]
        transaction.commit = m
        mock_function = MagicMock()
        @transaction_decorate(retry_delay=0.1)
        def write_db(self):
            mock_function(1)
            dbroot['db'] = 1

        write_db('self')

        self.assertEqual(dbroot['db'], 1)
        mock_function.assert_has_calls([call(1), call(1)])

        db.close()

    def test_set_installation(self):
        """
        Installation should be updated correctly
        """
        api.download = MagicMock()
        with managed(Database()) as db:
            self.assertIsNone(db.data.installation.id)
            db.set_installation(self.mock_installation, datetime.now())
            installation = db.data.installation
            self.assertEqual(installation.id, "1")
            self.assertIsNotNone(installation.ticket_templates)
            calls = [call("http://image4", os.path.join(settings.MEDIA_ROOT, 'images')),
                     call("http://image1", os.path.join(settings.MEDIA_ROOT, 'images')),
                     call("http://image2", os.path.join(settings.MEDIA_ROOT, 'images')),
                     call("http://image3", os.path.join(settings.MEDIA_ROOT, 'images'))]
            api.download.assert_has_calls(calls)

        # check it only download images if necessary
        with managed(Database()) as db:
            api.download = MagicMock()
            db.set_installation(self.mock_installation, datetime.now())
            self.assertFalse(api.download.called)
            mock_installation = deepcopy(self.mock_installation)
            mock_installation['scenario']['ticket_templates'][0]['image_variables'] = [{
                "owner": "test@figuredevices.com",
                "id": 1,
                "name": "Profession",
                "items": [
                    {
                        "image": "http://image5"
                    }]}]
            mock_installation['scenario']['ticket_templates'][0]['images'] = [{"image": "http://image6"}]
            db.set_installation(mock_installation, datetime.now())
            calls = [call("http://image5", os.path.join(settings.MEDIA_ROOT, 'images')),
                     call("http://image6", os.path.join(settings.MEDIA_ROOT, 'images'))]
            api.download.assert_has_calls(calls)

    def test_update_installation(self):
        """
        update_installation should set installation the first time
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.download = MagicMock()
        with managed(Database()) as db:
            db.set_installation = MagicMock()
            db.update_installation()
            self.assertTrue(db.set_installation.called)

    def test_update_installation_new_id(self):
        """
        installation should be updated if id changes
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.download = MagicMock()
        with managed(Database()) as db:
            db.update_installation()
            new_installation = deepcopy(self.mock_installation)
            db.set_installation = MagicMock()
            new_installation['id'] = 2
            api.get_installation = MagicMock(return_value=new_installation)
            db.update_installation()
            self.assertTrue(db.set_installation.called)

    def test_update_installation_not_modified(self):
        """
        update_installation should not update installation if it was not modified
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.download = MagicMock()
        with managed(Database()) as db:
            db.update_installation()
            db.set_installation = MagicMock()
            db.update_installation()
            self.assertFalse(db.set_installation.called)

    def test_update_installation_modified(self):
        """
        update_installation should update installation
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.download = MagicMock()
        with managed(Database()) as db:
            db.update_installation()
            mock_installation = deepcopy(self.mock_installation)
            mock_installation['scenario']['modified'] = "2015-05-12T08:31:01Z"
            api.get_installation = MagicMock(return_value=mock_installation)
            db.set_installation = MagicMock()
            db.update_installation()
            self.assertTrue(db.set_installation.called)
            mock_installation['scenario']['ticket_templates'][0]['modified'] = "2015-05-13T08:31:01Z"
            api.get_installation = MagicMock(return_value=mock_installation)
            db.set_installation = MagicMock()
            db.update_installation()
            self.assertTrue(db.set_installation.called)
            mock_installation['scenario']['ticket_templates']\
                .append(mock_installation['scenario']['ticket_templates'][0])
            api.get_installation = MagicMock(return_value=mock_installation)
            db.set_installation = MagicMock()
            db.update_installation()
            self.assertTrue(db.set_installation.called)

    def test_get_installation_return_none(self):
        """
        Installation should not be initialized if api return None
        """
        api.get_installation = MagicMock(return_value=None)
        api.get_codes = MagicMock(return_value=self.mock_codes)
        database = Database()
        with managed(database) as db:
            self.assertIsNone(db.data.installation.id)

    def test_get_installation_raise_exception(self):
        """
        Installation should not be initialized if get_installation raise Exception
        """
        api.get_installation = Mock(side_effect=api.ApiException)
        api.get_codes = MagicMock(return_value=self.mock_codes)
        database = Database()
        with managed(database) as db:
            self.assertIsNone(db.data.installation.id)

    def test_get_codes_raise_exception(self):
        """
        Installation should not be initialized if get_codes raise Exception
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_codes = Mock(side_effect=api.ApiException)
        database = Database()
        with managed(database) as db:
            self.assertIsNone(db.data.installation.id)

    def test_download_raise_exception(self):
        """
        Installation should not be initialized if download raise exception
        """
        api.download = Mock(side_effect=urllib2.HTTPError('', '', '', '', None))
        api.get_codes = MagicMock(return_value=self.mock_codes)
        api.get_installation = MagicMock(return_value=self.mock_installation)
        database = Database()
        with managed(database) as db:
            self.assertIsNone(db.data.installation.id)

    def test_claim_codes_if_necessary(self):
        """
        it should claim new codes from the api only if less than 1000 codes left
        """
        database = Database()
        with managed(database) as db:
            codes = ["AAAAA" for i in range(0, 2000)]
            api.claim_codes = MagicMock(return_value=codes)
            db.claim_new_codes_if_necessary()
            self.assertTrue(api.claim_codes.called)
            api.claim_codes = MagicMock(return_value=codes)
            db.claim_new_codes_if_necessary()
            self.assertFalse(api.claim_codes.called)
            for i in range(0, 1001):
                db.get_code()
            db.claim_new_codes_if_necessary()
            self.assertTrue(api.claim_codes.called)

    def test_get_code(self):
        """
        db.get_code should get a code and remove it from code list
        """
        with managed(Database()) as db:
            db.data.codes = ['00000', '00001']
            code = db.get_code()
            self.assertEqual(code, '00001')
            self.assertEqual(db.data.codes, ['00000'])

    def test_add_ticket(self):
        """
        db.add_ticket should add a ticket
        """
        api.download = MagicMock()
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_codes = MagicMock(return_value=['00000', '00001'])
        with managed(Database()) as db:
            db.update_installation()
            self.assertEqual(len(db.data.tickets), 0)
            now = datetime.now(pytz.timezone(settings.TIMEZONE))
            ticket = {
                'installation': '1',
                'snapshot': '/path/to/snapshot',
                'ticket': 'path/to/ticket',
                'dt': now,
                'code': 'JHUYG',
            }
            db.add_ticket(ticket)
            self.assertEqual(len(db.data.tickets), 1)
        with managed(Database()) as db:
            self.assertEqual(len(db.data.tickets), 1)

    def test_upload_tickets(self):
        """
        Uploading a ticket should upload all non uploaded tickets
        """
        api.create_ticket = MagicMock()
        with managed(Database()) as db:
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
            self.assertTrue(api.create_ticket.called)
            self.assertEqual([], db.data.tickets)

    def test_upload_tickets_raise_error(self):
        """
        upload_tickets should stop while loop if it throws an error
        """
        api.create_ticket = Mock(side_effect=Exception)
        with managed(Database()) as db:
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
        with managed(Database()) as db:
            self.assertEqual(len(db.data.tickets), 2)
