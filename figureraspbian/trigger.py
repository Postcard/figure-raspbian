import requests
import time
import os
import pifacedigitalio
from . import processus


TRIGGER_PIN = 0
SHUTDOWN_PIN = 2
REBOOT_PIN = 3


def shutdown(event):
    os.system("sudo shutdown -time now")


def reboot(event):
    os.system("sudo reboot")


refresh_listener = False


def trigger(event):
    processus.run()
    global refresh_listener
    refresh_listener = True

pifacedigital = pifacedigitalio.PiFaceDigital()


def get_listener():
    l = pifacedigitalio.InputEventListener(chip=pifacedigital)
    l.register(TRIGGER_PIN, pifacedigitalio.IODIR_RISING_EDGE, trigger, 100)
    l.register(SHUTDOWN_PIN, pifacedigitalio.IODIR_RISING_EDGE, shutdown)
    l.register(REBOOT_PIN, pifacedigitalio.IODIR_RISING_EDGE, reboot)
    l.activate()
    return l



if __name__ == '__main__':

    listener = get_listener()

    try:
        while True:
            if refresh_listener:
                listener.deactivate()
                listener = get_listener()
                refresh_listener = False
            time.sleep(1)
    except Exception as e:
        print e
    finally:
        listener.deactivate()