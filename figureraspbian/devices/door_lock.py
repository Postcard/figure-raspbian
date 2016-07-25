from pifacedigitalio import PiFaceDigital


class PiFaceDigitalDoorLock(object):
    """
    Represents an electrical lock such as this one https://www.amazon.fr/gp/product/B005FOTJF8/
    When the current is passing, the lock is opened.
    When the current is not passing the lock is closed.
    It is used to control the opening of a door that keep the devices safe
    In this implementation, the current from a 12V AC/DC converter is controlled via a PiFaceDigital relay
    """

    def __init__(self, pin=0):
        self.pifacedigital = PiFaceDigital()
        self.pin = pin

    def open(self):
        self.pifacedigital.relays[self.pin].turn_on()

    def close(self):
        self.pifacedigital.relays[self.pin].turn_off()

