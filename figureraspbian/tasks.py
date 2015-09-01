# -*- coding: utf8 -*-

from __future__ import absolute_import

import functools
from datetime import timedelta
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
from . import api


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
from requests.exceptions import RequestException

from .db import Database, managed

app = Celery('tasks', broker='amqp://guest@localhost//')

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'upload-ticket-every-minute-and-half': {
            'task': 'figureraspbian.tasks.upload_tickets',
            'schedule': timedelta(seconds=30)
        },
        'update-db-every-minute': {
            'task': 'figureraspbian.tasks.update_db',
            'schedule': timedelta(seconds=90)
        }
    },
    CELERY_TIMEZONE='UTC'
)


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    release_lock()
        return wrapper
    return task_exc


@single_instance_task(60 * 10)
@app.task
def upload_tickets():
    """ Upload all tickets that have not been previously updated"""
    with managed(Database()) as db:
        db.upload_tickets()


@app.task
def update_db():
    with managed(Database()) as db:
        db.update_installation()

@app.task
def set_paper_status(status):
    try:
        api.set_paper_status(status)
    except RequestException as e:
        logger.exception(e)