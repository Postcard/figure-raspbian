
from unittest import TestCase
from datetime import datetime
import mock

from .. import request


class RequestTestCase(TestCase):

    @mock.patch("figureraspbian.request.figure")
    def test_upload_portrait(self, mock_figure):
        """ it should upload a portrait to Figure API """

        with open("test_snapshot.jpg") as f:
            picture = f.read()
        with open("test_ticket.png") as f:
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
        with open("test_snapshot.jpg") as f:
            picture = f.read()
        with open("test_ticket.png") as f:
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
    @mock.patch("figureraspbian.models.settings")
    def test_update(self, settings, figure):
        """ it should fetch updated data from API and update local data """

        data = {
            "id": 1,
            "serial_number": "FIG.00012",
            "resin_uuid": "8c18223ebb19aa44cb23bc8e710de4f9",
            "place": {
                "id": 1,
                "name": "Atelier Commode",
                "tz": "Europe/Paris",
                "modified": "2017-03-17T09:09:03.268825Z"
            },
            "event": None,
            "ticket_template": {
                "id": 1,
                "modified": "2017-04-13T16:54:19.987969Z",
                "html": "<!doctype html></html>\n",
                "title": "Atelier Commode",
                "description": "",
                "text_variables": [],
                "image_variables": [],
                "images": [],
            }
        }
        figure.Photobooth.get.return_value = data
        from ..models import get_all_models
        from ..db import db
        from ..models import Photobooth
        db.database.create_tables(get_all_models(), True)
        uuid = "8c18223ebb19aa44cb23bc8e710de4f9"
        settings.RESIN_UUID = uuid
        Photobooth.get_or_create(uuid=uuid)
        request.update()
        updated = Photobooth.get()
        self.assertIsNotNone(updated.place)
        self.assertIsNotNone(updated.ticket_template)
        self.assertIsNotNone(updated.serial_number)


