from unittest import TestCase
import mock
import sys

RPi = mock.Mock()
sys.modules['RPi'] = RPi
RPi.GPIO = mock.Mock()
sys.modules['RPi.GPIO'] = RPi.GPIO

webkit2png = mock.Mock()
sys.modules['figureraspbian.webkit2png'] = webkit2png


from ..__main__ import ShutdownHook, create_tables
from ..db import db
from ..models import get_all_models


class MainTestCase(TestCase):

    @mock.patch("figureraspbian.__main__.Button")
    @mock.patch("figureraspbian.__main__.requests")
    @mock.patch("figureraspbian.__main__.settings")
    def test_shutdown_hook(self, settings, requests, Button):
        """ it should call resin io shutdown endpoint when power off is detected """
        button = mock.Mock()
        Button.factory.return_value = button
        settings.RESIN_SUPERVISOR_ADDRESS = 'resin_supervisor_address'
        settings.RESIN_SUPERVISOR_API_KEY = 'resin_supervisor_api_key'
        ShutdownHook()
        button.when_pressed()
        requests.post.assert_called_once_with("resin_supervisor_address/v1/shutdown?apikey=resin_supervisor_api_key",
                                              data={'force': True})

    def test_create_tables(self):
        """ it should create tables for all models """
        db.database.drop_tables(get_all_models(), safe=True)
        create_tables()
        self.assertEqual(len(db.database.get_tables()), 10)
