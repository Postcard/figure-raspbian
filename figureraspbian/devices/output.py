# -*- coding: utf8 -*-

try:
    from pifacedigitalio import PiFaceDigital
except ImportError:
    print "Could not find PiFaceDigital"


class PiFaceDigitalOutput(object):
    
    def __init__(self):
        
        self.pifacedigital = PiFaceDigital()
        self.pin = 0

    def turn_on(self):
        self.pifacedigital.relays[self.pin].turn_on()

    def turn_off(self):
        self.pifacedigital.relays[self.pin].turn_off()
