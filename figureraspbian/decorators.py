from figureraspbian.db import database


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
                return u'Oups we are busy, try again later'
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