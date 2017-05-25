
from unittest import TestCase
import mock
import sys
from datetime import datetime

RPi = mock.Mock()
sys.modules['RPi'] = RPi
RPi.GPIO = mock.Mock()
sys.modules['RPi.GPIO'] = RPi.GPIO
webkit2png = mock.Mock()
sys.modules['figureraspbian.webkit2png'] = webkit2png

from ..app import App


class AppTestCase(TestCase):

    @mock.patch("figureraspbian.app.is_online")
    @mock.patch("figureraspbian.app.download_booting_ticket_template")
    @mock.patch("figureraspbian.app.download_ticket_stylesheet")
    @mock.patch("figureraspbian.app.update")
    @mock.patch("figureraspbian.app.claim_new_codes_async")
    @mock.patch("figureraspbian.app.update_mac_addresses_async")
    @mock.patch("figureraspbian.app.get_photobooth")
    @mock.patch("figureraspbian.app.set_intervals")
    @mock.patch("figureraspbian.app.Button")
    def test_init_is_online(self, Button, set_intervals, get_photobooth, update_mac_addresses_async, claim_new_codes_async,
                            update, download_ticket_stylesheet, download_booting_ticket_template, is_online):
        is_online.return_value = True
        button = mock.Mock()
        Button.factory.return_value = button

        App()

        self.assertTrue(download_booting_ticket_template.called)
        self.assertTrue(download_ticket_stylesheet.called)
        self.assertTrue(update.called)
        self.assertTrue(claim_new_codes_async.called)
        self.assertTrue(update_mac_addresses_async.called)
        self.assertTrue(get_photobooth.called)
        self.assertTrue(set_intervals.called)

    @mock.patch("figureraspbian.app.is_online")
    @mock.patch("figureraspbian.app.get_photobooth")
    @mock.patch("figureraspbian.app.set_intervals")
    @mock.patch("figureraspbian.app.set_system_time")
    @mock.patch("figureraspbian.app.Button")
    @mock.patch("figureraspbian.app.RTC")
    def test_init_is_offline(self, RTC, Button, set_system_time, _1, _2, is_online):
        """ it should set clock from hardware clock"""
        is_online.return_value = False

        button = mock.Mock()
        Button.factory.return_value = button

        rtc = mock.Mock()
        RTC.factory.return_value = rtc

        dt = datetime(2017, 1, 1)
        rtc.read_datetime.return_value = dt

        App()

        set_system_time.assert_called_with(dt)






