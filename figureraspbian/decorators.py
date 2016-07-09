from figureraspbian.db import database


def execute_if_not_busy(lock):
    """
    This decorator prevents functions to be executed concurrently
    """
    def wrap(f):
        def newFunction(*args, **kwargs):
            if lock.acquire(False):
                try:
                    return f(*args, **kwargs)
                finally:
                    lock.release()
        return newFunction
    return wrap


def connection_managed(f):
    """
    This decorator ensure the database connection is opened before execution and closed after execution
    """

    def wrap(f):
        database.connect()
        try:
            f()
        finally:
            database.close()

    return wrap