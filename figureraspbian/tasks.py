# -*- coding: utf8 -*-

from __future__ import absolute_import

import functools
from datetime import timedelta
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


from django.conf import settings
settings.configure(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache'
        }
    }
)
from django.core.cache import cache
from celery import Celery
import transaction
from requests.exceptions import Timeout, ConnectionError

from .utils import internet_on
from .db import Database, managed

from . import api

app = Celery('tasks', broker='amqp://guest@localhost//')

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'upload-ticket-every-minute': {
            'task': 'figureraspbian.tasks.upload_tickets',
            'schedule': timedelta(seconds=60)
        },
        'update-db-every-minute': {
            'task': 'figureraspbian.tasks.update_db',
            'schedule': timedelta(seconds=60)
        }
    },
    CELERY_TIMEZONE='UTC'
)


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            print lock_id
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    release_lock()
        return wrapper
    return task_exc


@app.task
@single_instance_task(60*10)
def upload_tickets():
    if internet_on():
        with managed(Database()) as db:
            while True:
                if 'ticket' in db.data:
                    try:
                        ticket = db.data['ticket'].pop(0)
                        api.create_ticket(ticket)
                        transaction.commit()
                    except (IndexError, api.ApiException, Timeout, ConnectionError) as e:
                        logger.error(e)
                        break
                else:
                    break

@app.task
def update_db():
    if internet_on():
        with managed(Database()) as db:
            db.update()