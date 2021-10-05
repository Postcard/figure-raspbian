# -*- coding: utf8 -*-

from unittest import TestCase
import mock
from datetime import datetime
import sys

webkit2png = mock.Mock()
sys.modules['figureraspbian.webkit2png'] = webkit2png

from PIL import Image

from ..db import db
from ..models import get_all_models, Photobooth as PhotoboothModel, Code, TicketTemplate
from .. import settings
from ..photobooth import Photobooth
from ..exceptions import OutOfPaperError


class PhotoboothTestCase(TestCase):

    def setUp(self):
        db.connect_db()
        db.database.drop_tables(get_all_models(), safe=True)
        db.database.create_tables(get_all_models())
        PhotoboothModel.get_or_create(uuid=settings.RESIN_UUID)
        Code.create(value="CODE1")

    def tearDown(self):
        db.close_db()

    @mock.patch("figureraspbian.devices.camera.Camera.factory")
    @mock.patch("figureraspbian.devices.printer.Printer.factory")
    @mock.patch("figureraspbian.devices.door_lock.DoorLock.factory")
    def test_initialize(self, door_lock_factory, printer_factory, camera_factory):
        camera = mock.Mock()
        printer = mock.Mock()
        door_lock = mock.Mock()
        door_lock_factory.return_value = door_lock
        printer_factory.return_value = printer
        camera_factory.return_value = camera
        photobooth = Photobooth()
        camera.clear_space.assert_called_once()
        self.assertTrue(photobooth.ready)


    @mock.patch("figureraspbian.devices.camera.Camera.factory")
    @mock.patch("figureraspbian.devices.printer.Printer.factory")
    @mock.patch("figureraspbian.devices.door_lock.DoorLock.factory")
    def test_trigger_paper_empty(self, door_lock_factory, printer_factory, camera_factory):
        """ it should check if paper is present before taking a picture """
        camera = mock.Mock()
        printer = mock.Mock()
        door_lock = mock.Mock()
        door_lock_factory.return_value = door_lock
        printer_factory.return_value = printer
        camera_factory.return_value = camera

        printer.paper_present.return_value = False
        _p = PhotoboothModel.get()
        _p.paper_level = 0.0
        _p.save()
        photobooth = Photobooth()
        photobooth._trigger()

        self.assertEqual(camera.capture.call_count, 0)

        printer.paper_present.return_value = True
        snapshot = open("./test_snapshot.jpg").read()
        camera.capture.return_value = snapshot

        photobooth.render_print_and_upload = mock.Mock()
        photobooth._trigger()

        photobooth.render_print_and_upload.assert_called_with(snapshot)


    @mock.patch("figureraspbian.devices.camera.Camera.factory")
    @mock.patch("figureraspbian.devices.printer.Printer.factory")
    @mock.patch("figureraspbian.devices.door_lock.DoorLock.factory")
    @mock.patch("figureraspbian.photobooth.datetime")
    def test_set_context(self, mock_datetime, door_lock_factory, printer_factory, camera_factory):
        camera = mock.Mock()
        printer = mock.Mock()
        door_lock = mock.Mock()
        door_lock_factory.return_value = door_lock
        printer_factory.return_value = printer
        camera_factory.return_value = camera
        now = datetime(2017, 1, 1)
        mock_datetime.now.return_value = now

        photobooth = Photobooth()
        self.assertIsNone(photobooth.context)

        photobooth.set_context()
        expected = {'date': now, 'code': 'CODE1', 'counter': 0}
        self.assertEqual(photobooth.context, expected)


    @mock.patch("figureraspbian.devices.camera.Camera.factory")
    @mock.patch("figureraspbian.devices.printer.Printer.factory")
    @mock.patch("figureraspbian.devices.door_lock.DoorLock.factory")
    @mock.patch("figureraspbian.photobooth.Image")
    def test_render_ticket(self, mock_Image, door_lock_factory, printer_factory, camera_factory):
        """ it should resize picture and render ticket from context """
        camera = mock.Mock()
        printer = mock.Mock()
        door_lock = mock.Mock()
        door_lock_factory.return_value = door_lock
        printer_factory.return_value = printer
        camera_factory.return_value = camera

        picture = mock.Mock()
        mock_Image.open.return_value = picture
        picture.format = 'JPEG'
        picture.resize.return_value = Image.open('./test_snapshot.jpg')

        photobooth = Photobooth()
        now = datetime(2017, 1, 1)
        photobooth.context = {'date': now, 'code': 'CODE1', 'counter': 0}
        tt = {
            'title': 'foo',
            'description': 'bar',
            'html': '<html>{{title}}{{description}}</html>',
            'images': [],
            'image_variables': [],
            'text_variables': [],
            'modified': datetime(2016, 1, 1)
        }
        photobooth.photobooth.ticket_template = TicketTemplate.create(**tt)
        photobooth.photobooth.save()
        rendered = photobooth.render_ticket(open('./test_snapshot.jpg').read())

        size = settings.TICKET_TEMPLATE_PICTURE_SIZE
        picture.resize.assert_called_once_with((size, size))
        expected = "<html>foobar</html>"
        self.assertEqual(rendered, expected)


    @mock.patch("figureraspbian.devices.camera.Camera.factory")
    @mock.patch("figureraspbian.devices.printer.Printer.factory")
    @mock.patch("figureraspbian.devices.door_lock.DoorLock.factory")
    @mock.patch("figureraspbian.photobooth.webkit2png")
    @mock.patch("figureraspbian.photobooth.request")
    def test_render_print_and_upload(self, request, webkit2png, door_lock_factory, printer_factory, camera_factory):
        """ it should render a ticket, print it and upload it """
        camera = mock.Mock()
        printer = mock.Mock()
        door_lock = mock.Mock()
        door_lock_factory.return_value = door_lock
        printer_factory.return_value = printer
        camera_factory.return_value = camera

        webkit2png.get_screenshot.return_value = open('test_ticket.png').read()
        printer.print_image.return_value = 700

        p = PhotoboothModel.get()
        data = {
            "id": 1,
            "serial_number": "FIG.00001",
            "resin_uuid": "456d7e66247320147eda0a490df0c88a170f60f4378c7c1e3e77f845963c2e",
            "place": {
                "id": 128,
                "name": "Le Bar à Bulles",
                "tz": "Europe/Paris",
                "modified": "2017-05-04T09:33:21.988428Z"
            },
            "event": None,
            "ticket_template": {
                "id": 475,
                "modified": "2017-01-27T08:53:15Z",
                "html": "<!doctype html>{{title}}{{description}}</html>",
                "title": "Bar à Bulles",
                "description": "La Machine du Moulin Rouge",
                "text_variables": [],
                "image_variables": [],
                "images": [],
            }
        }

        p.update_from_api_data(data)
        picture = open("./test_snapshot.jpg").read()

        photobooth = Photobooth()
        photobooth.render_print_and_upload(picture)

        expected = '<!doctype html>Bar \xe0 BullesLa Machine du Moulin Rouge</html>'
        webkit2png.get_screenshot.assert_called_once_with(expected)

        self.assertEqual(printer.print_image.call_count, 1)

        self.assertEqual(photobooth.counter, 1)
        self.assertAlmostEqual(photobooth.paper_level, 99.88, delta=0.1)

        self.assertEqual(request.upload_portrait_async.call_count, 1)
        request.update_paper_level_async.assert_called_with(photobooth.paper_level)


    @mock.patch("figureraspbian.devices.camera.Camera.factory")
    @mock.patch("figureraspbian.devices.printer.Printer.factory")
    @mock.patch("figureraspbian.devices.door_lock.DoorLock.factory")
    @mock.patch("figureraspbian.photobooth.webkit2png")
    @mock.patch("figureraspbian.photobooth.request")
    def test_render_print_and_upload_out_of_paper(self, request, webkit2png, door_lock_factory,
                                                  printer_factory, camera_factory):
        """ it should catch OutOfPaperException and set paper level to 0 """
        camera = mock.Mock()
        printer = mock.Mock()
        door_lock = mock.Mock()
        door_lock_factory.return_value = door_lock
        printer_factory.return_value = printer
        camera_factory.return_value = camera

        webkit2png.get_screenshot.return_value = open('test_ticket.png').read()
        printer.print_image.side_effect = [OutOfPaperError]

        p = PhotoboothModel.get()
        data = {
            "id": 1,
            "serial_number": "FIG.00001",
            "resin_uuid": "456d7e66247320147eda0a490df0c88a170f60f4378c7c1e3e77f845963c2e",
            "place": {
                "id": 128,
                "name": "Le Bar à Bulles",
                "tz": "Europe/Paris",
                "modified": "2017-05-04T09:33:21.988428Z"
            },
            "event": None,
            "ticket_template": {
                "id": 475,
                "modified": "2017-01-27T08:53:15Z",
                "html": "<!doctype html>{{title}}{{description}}</html>",
                "title": "Bar à Bulles",
                "description": "La Machine du Moulin Rouge",
                "text_variables": [],
                "image_variables": [],
                "images": [],
            }
        }

        p.update_from_api_data(data)
        picture = open("./test_snapshot.jpg").read()

        photobooth = Photobooth()
        photobooth.render_print_and_upload(picture)

        self.assertEqual(photobooth.paper_level, 0.0)
        request.update_paper_level_async.assert_called_with(photobooth.paper_level)













