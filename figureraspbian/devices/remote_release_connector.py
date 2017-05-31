
import time

from pifacedigitalio import PiFaceDigital
import gpiozero

from .. import settings
from ..exceptions import InvalidIOInterfaceError


class RemoteReleaseConnector(object):

    def __init__(self, pin):
        self.pin = pin

    def trigger(self):
        raise NotImplementedError()

    def factory(*args, **kwargs):
        if settings.IO_INTERFACE == 'PIFACE':
            return PiFaceRemoteReleaseConnector(*args, **kwargs)
        elif settings.IO_INTERFACE == 'GPIOZERO':
            return GPIOZeroRemoteReleaseConnector(*args, **kwargs)
        else:
            raise InvalidIOInterfaceError()

    factory = staticmethod(factory)


class PiFaceRemoteReleaseConnector(RemoteReleaseConnector):

    def __init__(self, *args, **kwargs):
        super(PiFaceRemoteReleaseConnector, self).__init__(*args, **kwargs)
        self.pifacedigital = PiFaceDigital()

    def trigger(self):
        self.pifacedigital.relays[self.pin].turn_on()
        time.sleep(0.1)
        self.pifacedigital.relays[self.pin].turn_off()


class GPIOZeroRemoteReleaseConnector(RemoteReleaseConnector):

    def __init__(self, *args, **kwargs):
        super(GPIOZeroRemoteReleaseConnector, self).__init__(*args, **kwargs)
        self.device = gpiozero.OutputDevice(self.pin)

    def trigger(self):
        self.device.on()
        time.sleep(0.1)
        self.device.off()
