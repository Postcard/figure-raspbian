import time
import sys
import pifacedigitalio
from . import processus, settings, celery, utils
from .db import Database, managed

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

    # start celery
    celery.app.start()

    # Make sure database is correctly initialized
    with managed(Database(settings.ENVIRONMENT)) as db:
        if utils.internet_on():
            db.update()
        elif db.is_initialized():
            pass
        else:
            sys.exit('Database is not initialized')

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


