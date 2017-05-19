# -*- coding: utf8 -*-

from .db import database
from .exceptions import DevicesBusy

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


def connection_managed(f):
    """
    This decorator ensures the database connection is opened before execution and closed after execution
    """
    def wrap(f):
        database.connect()
        try:
            f()
        finally:
            database.close()
    return wrap