# -*- coding: utf8 -*-

from exceptions import DevicesBusy


def execute_if_not_busy(lock):
    """
    This decorator prevents a function to be executed concurrently
    """
    def wrap(f):
        def decorated(*args, **kwargs):
            if lock.acquire(False):
                try:
                    return f(*args, **kwargs)
                finally:
                    lock.release()
            else:
                raise DevicesBusy()
        return decorated
    return wrap