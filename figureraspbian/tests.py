# coding=utf-8

import unittest
import re
import os
from datetime import datetime
import pytz
from .ticketrenderer import TicketRenderer
from .utils import url2name
from .db import Database, NotInitializedError, managed
from . import api, settings, processus
from mock import MagicMock


class TestTicketRenderer(unittest.TestCase):

    def setUp(self):
        installation = '1'
        html = '{{snapshot}} {{code}} {{datetime | datetimeformat}} {{textvariable_1}} {{imagevariable_2}} {{image_1}}'
        self.chiefs = ['Titi', 'Vicky', 'Benni']
        self.chiefs = [{'id': '1', 'text': 'Titi'}, {'id': '2', 'text': 'Vicky'}, {'id': '3', 'text': 'Benni'}]
        text_variables = [{'id': '1', 'items': self.chiefs}]
        self.paths = [{'id': '1', 'media': '/path/to/variable/image1'}, {'id': '2', 'media': '/path/to/variable/image2'}]
        image_variables = [{'id': '2', 'items': self.paths}, {'id': '3', 'items': []}]
        images = [{'id': '1', 'media': 'path/to/image'}]
        self.ticket_renderer = TicketRenderer(html, text_variables, image_variables, images)

    def test_random_selection(self):
        """
        random selection should randomly select variable items
        """
        random_text_selections, random_image_selections = self.ticket_renderer.random_selection()
        self.assertTrue(len(random_text_selections), 1)
        self.assertEqual(random_text_selections[0][0], '1')
        self.assertTrue(random_text_selections[0][1] in self.chiefs)
        self.assertTrue(len(random_image_selections), 1)
        self.assertEqual(random_image_selections[0][0], '2')
        self.assertTrue(random_image_selections[0][1] in self.paths)

    def test_code(self):
        """
        generics function should return a proper code
        """
        _, code = self.ticket_renderer.generics('1')
        self.assertTrue(len(code) == 8)
        self.assertTrue(code.isupper())

    def test_render(self):
        """
        TicketRenderer should render a ticket
        """
        rendered_html, _, _, _, _ = self.ticket_renderer.render('1', '/path/to/snapshot')
        expected = re.compile("/path/to/snapshot \w{8} \d{4}-\d{2}-\d{2} (Titi|Vicky|Benni) /path/to/variable/image(1|2) path/to/image")
        self.assertRegexpMatches(rendered_html, expected)

    def test_set_date_format(self):
        """
        Ticket renderer should handle datetimeformat filter
        """
        html = '{{datetime | datetimeformat("%Y")}}'
        self.ticket_renderer.html = html
        rendered_html, _, _, _, _ = self.ticket_renderer.render('1', '/path/to/snapshot')
        self.assertRegexpMatches(rendered_html, re.compile("\d{4}"))

    def test_encode_non_unicode_character(self):
        """
        Ticket renderer should encode non unicode character
        """
        html = "Du texte avec un accent ici: é"
        self.ticket_renderer.html = html
        rendered_html, _, _, _, _ = self.ticket_renderer.render('1', '/path/to/snapshot')
        self.assertTrue(u'Du texte avec un accent ici: é' in rendered_html)


class TestUtilityFunction(unittest.TestCase):

    def test_url2name(self):
        """
        url2name should extract file name in url
        """
        name = url2name('http://api.figuredevices.com/static/css/ticket.css')
        self.assertEqual(name, 'ticket.css')


class TestApi(unittest.TestCase):

    def test_get_installation(self):
        """
        api should get installation
        """
        installation = api.get_installation()
        self.assertTrue('scenario_obj' in installation)
        self.assertTrue('start' in installation)
        self.assertTrue('end' in installation)
        self.assertTrue('place' in installation)

    def test_get_scenario(self):
        """
        api should get scenario
        """
        scenario = api.get_scenario('1')
        self.assertTrue('name' in scenario)
        self.assertTrue('ticket_template' in scenario)
        ticket_template = scenario['ticket_template']
        self.assertTrue('images_objects' in ticket_template)
        self.assertTrue('text_variables_objects' in ticket_template)
        self.assertTrue('image_variables_objects' in ticket_template)

    def test_download(self):
        """
        api should correctly download a file
        """
        downloaded = api.download('static/snapshots/example.jpg', settings.SNAPSHOT_DIR)
        self.assertEqual(os.path.basename(downloaded), 'example.jpg')

    def test_download_when_redirect(self):
        """
        api should correctly download a file when redirect
        """
        downloaded = api.download('snapshots/example/', settings.SNAPSHOT_DIR)
        self.assertEqual(os.path.basename(downloaded), 'example.jpg')

    def test_create_random_text_selection(self):
        """
        api should create a random text selection
        """
        created = api.create_random_text_selection('1', '1')
        self.assertIsNotNone(created)

    def test_create_random_image_selection(self):
        """
        api should create a random text selection
        """
        created = api.create_random_image_selection('1', '1')
        self.assertIsNotNone(created)

    def test_create_ticket(self):
        """
        api should create ticket
        """
        snapshot_path = "%s/resources/2_20150331.jpg" % settings.FIGURE_DIR
        ticket_path = snapshot_path # for testing purposes
        code = '8HDT54D7'
        dt = datetime.now(pytz.timezone(settings.TIMEZONE))
        random_text_selections = ['1']
        random_image_selections = ['1']
        created = api.create_ticket(snapshot_path, ticket_path, dt, code,
                                    random_text_selections, random_image_selections)
        self.assertIsNotNone(created)


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.mock_installation = {
            "scenario_obj": {
                "id": 1,
            },
            "place": None,
            "start": "2016-07-01T12:00:00Z",
            "end": "2016-07-02T12:00:00Z"
        }

        self.mock_scenario = {
            "name": "Marabouts",
            "ticket_template": {
                "html": "<html></html>",
                "text_variables_objects": [
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
                "image_variables_objects": [
                    {
                        "owner": "test@figuredevices.com",
                        "id": 1,
                        "name": "animaux",
                        "items": [
                            {
                                "id": 2,
                                "media": "http://api-integration.figuredevices.com/media/images/1427817820717.jpg",
                                "variable": 1
                            }
                        ]
                    }
                ],
                "images_objects": [
                    {
                        "id": 2,
                        "media": "http://api-integration.figuredevices.com/media/images/1427817820718.jpg",
                        "variable": None
                    }
                ]
            }
        }

    def test_initialization(self):
        """
        Database should not be initialized when first created
        """
        database = Database('development')
        with managed(database) as db:
            self.assertFalse(db.is_initialized())
            db.clear()

    def test_raise_not_initialized_error(self):
        """
        Database should raise exception when not initialized and trying to access data
        """
        database = Database('development')
        with managed(database) as db:
            with self.assertRaises(NotInitializedError):
                db.installation()
                db.clear()

    def test_update(self):
        """
        Database should update
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database) as db:
            db.update()
            api.get_scenario.assert_called_with(1)
            self.assertTrue(db.is_initialized())
            db.clear()

    def test_installation(self):
        """
        Database should return installation
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database) as db:
            db.update()
            self.assertIsNotNone(db.installation())
            db.clear()

    def test_scenario(self):
        """
        Database should return scenario
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database) as db:
            db.update()
            self.assertIsNotNone(db.scenario())
            db.clear()

    def test_ticket_template(self):
        """
        Database should return ticket template
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database) as db:
            db.update()
            self.assertIsNotNone(db.ticket_template())
            db.clear()

    def test_text_variables(self):
        """
        Database should return text variables
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database) as db:
            db.update()
            self.assertTrue(len(db.text_variables()), 1)
            db.clear()

    def test_image_variables(self):
        """
        Database should return image variables
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database)as db:
            db.update()
            self.assertTrue(len(db.image_variables()), 1)
            db.clear()

    def test_images(self):
        """
        Database should return images
        """
        api.get_installation = MagicMock(return_value=self.mock_installation)
        api.get_scenario = MagicMock(return_value=self.mock_scenario)
        api.download = MagicMock()
        database = Database('development')
        with managed(database) as db:
            db.update()
            self.assertTrue(len(db.images()), 1)
            db.clear()


class TestProcessus(unittest.TestCase):

    def test_processus(self):
        """
        Processus should execute successfully
        """
        with managed(Database('development')) as db:
            db.update()
        processus.run()

if __name__ == '__main__':
    unittest.main()





