import time
import pifacedigitalio
from . import processus, settings
from . import settings


refresh_listener = False

def trigger(event):
    processus.run()
    global refresh_listener
    refresh_listener = True


pifacedigital = pifacedigitalio.PiFaceDigital()



def get_listener():
    l = pifacedigitalio.InputEventListener(chip=pifacedigital)
    l.register(settings.TRIGGER_PIN, pifacedigitalio.IODIR_RISING_EDGE, trigger, 100)
    l.activate()
    return l


if __name__ == '__main__':

    # make sure database is correctly

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



















if __name__ == '__main__':


