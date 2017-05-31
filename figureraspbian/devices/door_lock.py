
from pifacedigitalio import PiFaceDigital
import gpiozero

from .. import settings
from ..exceptions import InvalidIOInterfaceError


class DoorLock(object):
    """
    Represents an electrical lock such as this one https://www.amazon.fr/gp/product/B005FOTJF8/
    When the current is passing, the lock is opened.
    When the current is not passing the lock is closed.
    It is used to control the opening of a door that keep the devices safe
    """

    def open(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def factory(*args, **kwargs):
        if settings.IO_INTERFACE == 'PIFACE':
            return PiFaceDigitalDoorLock(*args, **kwargs)
        elif settings.IO_INTERFACE == 'GPIOZERO':
            return GPIOZeroDoorLock()
        else:
            raise InvalidIOInterfaceError()

    factory = staticmethod(factory)


class PiFaceDigitalDoorLock(DoorLock):
    """
    In this implementation, the current from a 12V AC/DC converter is controlled via a PiFaceDigital relay
    """

    def __init__(self, pin=0):
        self.pifacedigital = PiFaceDigital()
        self.pin = pin

    def open(self):
        self.pifacedigital.relays[self.pin].turn_on()

    def close(self):
        self.pifacedigital.relays[self.pin].turn_off()


class GPIOZeroDoorLock(DoorLock):
    """
    In this implementation, the current from a 12V AC/DC converter is controlled via an external relay driven by a gpio
    """

    def __init__(self, pin=0):
        self.device = gpiozero.OutputDevice(pin)

    def open(self):
        self.device.on()

    def close(self):
        self.device.off()
