# -*- coding: utf8 -*-
try:
    from pifacedigitalio import PiFaceDigital
except ImportError:
    print "Could not find PiFaceDigital"

from .. import settings


class PiFaceDigitalInput(object):

    def __init__(self):

        self.pifacedigital = PiFaceDigital()
        self.pin = settings.TRIGGER_PIN

    def get_value(self):
        return self.pifacedigital.input_pins[self.pin].value