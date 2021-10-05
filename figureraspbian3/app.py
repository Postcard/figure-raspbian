# -*- coding: utf8 -*-
import logging
from .threads import Interval, rlock
import socket

from . import settings
from .devices.button import Button
from .devices.real_time_clock import RTC
from .api import start_server
from .exceptions import OutOfPaperError
from .photobooth import get_photobooth

from .request import is_online, download_booting_ticket_template, download_ticket_stylesheet, update, upload_portraits
from .request import claim_new_codes, update_mac_addresses_async
from .utils import set_system_time


logger = logging.getLogger(__name__)


class App(object):
    """ Registers button callbacks and make sure resources are correctly initialized and closed """

    def __init__(self):

        if is_online():
            try:
                download_ticket_stylesheet()
                download_booting_ticket_template()
            except Exception as e:
                logger.exception(e)

            try:
                update()
            except Exception as e:
                logger.exception(e)

            update_mac_addresses_async()

            try:
                claim_new_codes()
            except Exception as e:
                logger.exception(e)
        else:
            rtc = RTC.factory()
            if rtc:
                try:
                    hc_dt = rtc.read_datetime()
                    set_system_time(hc_dt)
                except Exception as e:
                    logger.exception(e)
        self.photobooth = get_photobooth()
        self.button = Button.factory(settings.BUTTON_PIN, 0.05, settings.DOOR_OPENING_DELAY)
        self.button.when_pressed = self.when_pressed
        self.button.when_held = self.when_held
        self.intervals = set_intervals()

    def when_pressed(self):
        self.photobooth.trigger_async()

    def when_held(self):
        self.photobooth.unlock_door()

    def start(self):
        self.button.start()
        try:
            self.photobooth.print_booting_ticket()
        except OutOfPaperError:
            pass
        logger.info("Ready...")
        try:
            start_server()
        except socket.error as e:
            logger.exception(e)

    def stop(self):
        for interval in self.intervals:
            interval.stop()
        self.button.close()
        # wait for a trigger to complete before exiting
        rlock.acquire()
        logger.info("Bye Bye")


def set_intervals():
    """ Start tasks that are run in the background at regular intervals """
    intervals = [
        Interval(update, settings.UPDATE_POLL_INTERVAL),
        Interval(upload_portraits, settings.UPLOAD_PORTRAITS_INTERVAL),
        Interval(claim_new_codes, settings.CLAIM_NEW_CODES_INTERVAL)
    ]

    for interval in intervals:
        interval.start()

    return intervals