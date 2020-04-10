# -*- coding: utf8 -*-
import inspect
from functools import wraps
from threading import Event
import logging

from pifacedigitalio import PiFaceDigital
import gpiozero

from threads import StoppableThread
import settings
from exceptions import InvalidIOInterfaceError

logger = logging.getLogger(__name__)


class BadEventHandler(Exception):
    pass


class Button(object):
    """
    Represents the push button that is used to trigger the devices
    It registers two optional callback "when_pressed" and "when_held" that are fired respectively when the
    button is pressed and when the button is held
    """

    def __init__(self, pin, bounce_time, hold_time, pull_up=True):
        super(Button, self).__init__()
        self.pin = pin
        self.bounce_time = bounce_time
        self.hold_time = hold_time
        self.pull_up = pull_up
        self._active_event = Event()
        self._inactive_event = Event()
        self._holding = Event()
        self._when_pressed = None
        self._when_unpressed = None
        self._when_held = None
        self._last_state = None
        self._event_thread = EventThread(self)
        self._hold_thread = HoldThread(self)

    def start(self):
        self._event_thread.start()
        self._hold_thread.start()

    def value(self):
        raise NotImplementedError()

    @property
    def when_pressed(self):
        return self._when_pressed

    @when_pressed.setter
    def when_pressed(self, value):
        self._when_pressed = self._wrap_callback(value)

    @property
    def when_unpressed(self):
        return self._when_unpressed

    @when_unpressed.setter
    def when_unpressed(self, value):
        self._when_unpressed = self._wrap_callback(value)

    @property
    def when_held(self):
        return self._when_held

    @when_held.setter
    def when_held(self, value):
        self._when_held = self._wrap_callback(value)

    def _wrap_callback(self, fn):
        if fn is None:
            return None
        elif not callable(fn):
            raise BadEventHandler('value must be None or a callable')
        elif inspect.isbuiltin(fn):
            # We can't introspect the prototype of builtins. In this case we
            # assume that the builtin has no (mandatory) parameters;
            return fn
        else:
            # Try binding ourselves to the argspec of the provided callable.
            # If this works, assume the function is capable of accepting no
            # parameters
            try:
                inspect.getcallargs(fn)
                return fn
            except TypeError:
                try:
                    # If the above fails, try binding with a single parameter
                    # (ourselves). If this works, wrap the specified callback
                    inspect.getcallargs(fn, self)
                    @wraps(fn)
                    def wrapper():
                        return fn(self)
                    return wrapper
                except TypeError:
                    raise BadEventHandler(
                        'value must be a callable which accepts up to one '
                        'mandatory parameter')

    def _fire_activated(self):
        logger.info("Button pressed")
        if self.when_pressed:
            self.when_pressed()

    def _fire_deactivated(self):
        logger.info("Button unpressed")
        if self.when_unpressed:
            self.when_unpressed()

    def _fire_held(self):
        logger.info("Button held")
        if self.when_held:
            self.when_held()

    def close(self):
        self._event_thread.stop()
        self._hold_thread.stop()

    def factory(*args, **kwargs):
        if settings.IO_INTERFACE == 'PIFACE':
            return PiFaceDigitalButton(*args, **kwargs)
        elif settings.IO_INTERFACE == 'GPIOZERO':
            return GPIOZeroButton(*args, **kwargs)
        raise InvalidIOInterfaceError()

    factory = staticmethod(factory)


class PiFaceDigitalButton(Button):
    """
    Represents a button that is connected to the GPIO pins of the Raspberry Pi with a PiFaceDigital IO board
    See http://www.piface.org.uk/products/piface_digital/ for more information
    """

    def __init__(self, *args, **kwargs):
        self.pifacedigital = PiFaceDigital()
        super(PiFaceDigitalButton, self).__init__(*args, **kwargs)

    def value(self):
        return self.pifacedigital.input_pins[self.pin].value


class GPIOZeroButton(Button):
    """ Represents a button whose value is determined using the GPIOZero library """

    def __init__(self, *args, **kwargs):
        super(GPIOZeroButton, self).__init__(*args, **kwargs)
        self.device = gpiozero.Button(self.pin, pull_up=self.pull_up)

    def value(self):
        return self.device.is_pressed


class EventThread(StoppableThread):
    """
    Provides a background thread that repeatedly check for button edges events (activated or deactivated)
    """

    def __init__(self, parent):
        super(EventThread, self).__init__(target=self.event, args=(parent,))

    def event(self, parent):
        while not self.stopping.wait(parent.bounce_time):
            self._fire_events(parent)

    def _fire_events(self, parent):
        old_state = parent._last_state
        new_state = parent._last_state = parent.value()
        if old_state is None:
            # Initial "indeterminate" state; set events but don't fire
            # callbacks as there's not necessarily an edge
            if new_state:
                parent._active_event.set()
            else:
                parent._inactive_event.set()
        elif old_state != new_state:
            if new_state:
                parent._inactive_event.clear()
                parent._active_event.set()
                parent._holding.set()
                parent._fire_activated()
            else:
                parent._active_event.clear()
                parent._inactive_event.set()
                parent._fire_deactivated()


class HoldThread(StoppableThread):
    """
    Provides a background thread that repeatedly check if the button is held
    """
    def __init__(self, parent):
        super(HoldThread, self).__init__(target=self.held, args=(parent,))

    def held(self, parent):
        while not self.stopping.is_set():
            if parent._holding.wait(0.1):
                parent._holding.clear()
                if not (
                        self.stopping.is_set() or
                        parent._inactive_event.wait(parent.hold_time)
                        ):
                    parent._fire_held()





