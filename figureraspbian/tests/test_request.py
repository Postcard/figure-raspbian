
from unittest import TestCase
from datetime import datetime
import mock

from .. import request
from .. import settings


class RequestTestCase(TestCase):

    @mock.patch("figureraspbian.request.figure")
    def test_upload_portrait(self, mock_figure):
        """ it should upload a portrait to Figure API """

        with open("test_snapshot.jpg", 'rb') as f:
            picture = f.read()
        with open("test_ticket.png", 'rb') as f:
            ticket = f.read()

        portrait = {
            'picture': picture,
            'ticket': ticket,
            'taken': datetime(2017, 1, 1),
            'place': 1,
            'event': 1,
            'photobooth': 1,
            'code': "CODE1",
            'filename': "Figure.jpg"
        }
        request.upload_portrait(portrait)
        expected_data = {'taken': portrait['taken'], 'code': portrait['code'], 'place': portrait['place'],
                         'event': portrait['event'], 'photobooth': portrait['photobooth']}
        expected_files = {
            'picture_color': (portrait['filename'], portrait['picture']),
            'ticket': (portrait['filename'], portrait['ticket'])
        }
        mock_figure.Portrait.create.assert_called_once_with(files=expected_files, data=expected_data)

    @mock.patch("figureraspbian.request.figure")
    @mock.patch("figureraspbian.request.utils.write_file")
    @mock.patch("figureraspbian.request.Portrait")
    def test_upload_portrait_raise_exception(self, mock_Portrait, mock_write_file, mock_figure):
        """ it should save portrait to local file system """
        with open("test_snapshot.jpg", 'rb') as f:
            picture = f.read()
        with open("test_ticket.png", 'rb') as f:
            ticket = f.read()

        portrait = {
            'picture': picture,
            'ticket': ticket,
            'taken': datetime(2017, 1, 1),
            'place': 1,
            'event': 1,
            'photobooth': 1,
            'code': "CODE1",
            'filename': "Figure.jpg"
        }

        class MyException(Exception):
            pass

        mock_figure.Portrait.create.side_effect = [MyException()]

        request.upload_portrait(portrait)

        self.assertEqual(mock_write_file.call_count, 2)
        self.assertEqual(mock_Portrait.create.call_count, 1)

    @mock.patch("figureraspbian.request.figure")
    @mock.patch("figureraspbian.request.Code")
    def test_claim_new_codes(self, mock_Code, mock_figure):
        """ it should claim new codes from API if less than 100 codes left """
        mock_Code.less_than_1000_left.return_value = True
        codes = ["%05d" % i for i in range(0, 1000)]
        mock_figure.Code.claim.return_value = codes
        request.claim_new_codes()
        mock_Code.bulk_insert.assert_called_once_with(codes)

    @mock.patch("figureraspbian.request.figure")
    # @mock.patch("figureraspbian.models.settings")
    def test_update(self, figure):
        """ it should fetch updated data from API and update local data """

        data = {
            "id": 19,
            "serial_number": "FIG.00012",
            "resin_uuid": "fhqQkiON7ZbgZE9ejLBQLn7c2D8vYy",
            "place": {
                "id": 47,
                "name": "Figure",
                "slug": "figure",
                "link": None,
                "google_places_id": "ChIJJ7fFF_Zt5kcRAUZ48Xo2_Dw",
                "tz": "Europe/Paris",
                "photobooth_count": 3,
                "gif": None,
                "modified": "2020-03-07T23:01:37.001839Z",
                "code": "D48E",
                "color_portraits": False,
                "portraits_expiration": 30
            },
            "event": None,
            "ticket_template": {
                "id": 593,
                "modified": "2020-03-03T15:03:59.500973Z",
                "html": "<!doctype html>\n<html class=\"figure-ticket-container\">\n  <head>\n    <meta charset=\"utf-8\">\n    <link rel=\"stylesheet\" href=\"{{css_url}}\">\n  </head>\n  <body class=\"figure-ticket-container\"\">\n    <div class=\"figure-ticket\">\n      <div class=\"figure-header\" style=\"text-align: center;\">\n        <img class=\"figure-image\" src={{image_2103}}>\n        <p><br>{% if description %}<span class=\"figure-description\">{{description}}</span><br>{% endif %}<span class=\"figure-generic-variable figure-datetime\">{{datetime|datetimeformat()}}</span><br><br></p>\n      </div>\n      <div class=\"figure-snapshot-container\">\n        <img class=\"figure-snapshot\" src={{picture}}>\n      </div>\n      <div class=\"figure-footer\" style=\"text-align: center;\">\n        <p><br>jaiunticket.com<br>n°<span class=\"figure-generic-variable figure-code\">{{code}}</span>\n        </p>\n      </div>\n    </div>\n  </body>\n</html>",
                "title": "",
                "description": "Test RTC et alimentation 24V",
                "text_variables": [],
                "image_variables": [],
                "images": [],
                "is_custom": False,
            },
        }
        figure.Photobooth.get.return_value = data
        from ..models import get_all_models
        from ..db import db
        from ..models import Photobooth
        db.database.create_tables(get_all_models(), safe=True)
        uuid = "fhqQkiON7ZbgZE9ejLBQLn7c2D8vYy"
        # import os
        # os.environ['RESIN_UUID'] = uuid
        settings.RESIN_UUID = uuid
        photobooth, created = Photobooth.get_or_create(uuid=uuid)
        request.update()
        updated = Photobooth.get()
        # print (updated.place)
        # print (updated.serial_number)
        self.assertIsNotNone(updated.place)
        self.assertIsNotNone(updated.ticket_template)
        self.assertIsNotNone(updated.serial_number)


