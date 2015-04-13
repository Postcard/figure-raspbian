# -*- coding: utf8 -*-

import time
from threading import Thread


try:
    import pifacedigitalio
except ImportError:
    print("Could not import pifacedigitalio")


class BlinkingTask(object):

    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def run(self, output, init_state, t):
        state = init_state
        while self._running:
            output.set(state)
            time.sleep(t)
            state = not state


class Output(object):
    """ Output interface """

    def set(self, state):
        """ Set the value of the output, either True or False """
        raise NotImplementedError

    def blink(self, init_state=False, t=0.5):
        """ Blink the output """
        b = BlinkingTask()
        t = Thread(target=b.run, args=(self, init_state, t))
        t.start()
        return b


class PiFaceOutput(Output):
    """
    Output using the PiFace digital board.
    PiFace digital is a small board that plug on to the GPIO of the Raspberry Pi, allowing
    to sense and control the real world
    http://www.piface.org.uk/products/piface_digital/
    http://piface.github.io/pifacedigitalio/pifacedigital.html#outputs
    """

    def __init__(self, pin=7, init=True):
        self.pifacedigital = pifacedigitalio.PiFaceDigital()
        self.pin = pin
        self.set(init)

    def set(self, state):
        if state:
            self.pifacedigital.output_pins[self.pin].turn_on()
        else:
            self.pifacedigital.output_pins[self.pin].turn_off()


class DummyOutput(Output):
    """
    Output used for test purposes. It prints its state to the console.
    """

    def __init__(self):
        pass

    def set(self, state):
        stmt = "Setting output state to {state}".format(state=state)
        print(stmt)
