# -*- coding: utf8 -*-

try:
    import pifacedigitalio
except ImportError:
    print("Could not import pifacedigitalio")


class Light(object):
    """ A Light is able to flash """

    def flash_on(self):
        raise NotImplementedError()

    def flash_off(self):
        raise NotImplementedError()


class LEDPanelLight(Light):

    pifacedigital = pifacedigitalio.PiFaceDigital()

    def flash_on(self):
        self.pifacedigital.output_pins[0].turn_on()

    def flash_off(self):
        self.pifacedigital.output_pins[0].turn_off()


class DummyLight(Light):

    def flash_on(self):
        print "flash on"

    def flash_off(self):
        print "flash off"




