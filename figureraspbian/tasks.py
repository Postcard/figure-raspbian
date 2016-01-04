# -*- coding: utf8 -*-

from __future__ import absolute_import

import functools
from datetime import timedelta
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
from . import api, settings
from os.path import join

from django.conf import settings as django_settings

django_settings.configure(
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

app = Celery('tasks', broker='redis://localhost:6379/0')

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'upload-tickets': {
            'task': 'figureraspbian.tasks.upload_tickets',
            'schedule': timedelta(seconds=120)
        },
        'update-db-every-minute-and-half': {
            'task': 'figureraspbian.tasks.update_db',
            'schedule': timedelta(seconds=90)
        },
        'pack-db-every-hour': {
            'task': 'figureraspbian.tasks.pack_db',
            'schedule': timedelta(hours=1)
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
def set_paper_status(status, printed_paper_length):
    try:
        api.set_paper_status(status, printed_paper_length)
    except RequestException as e:
        logger.exception(e)

@app.task
def upload_ticket(ticket):
    """ Upload a ticket or add to tickets list"""
    try:
        # try uploading the ticket
        api.create_ticket(ticket)
    except Exception as e:
        logger.error(e)
        # Couldn't upload the ticket, save files to filesystem and add ticket to the db for schedule upload
        snapshot_path = join(settings.MEDIA_ROOT, 'snapshots', ticket['filename'])
        with open(snapshot_path, "wb") as f:
            f.write(ticket['snapshot'])
        ticket['snapshot'] = snapshot_path

        ticket_path = join(settings.MEDIA_ROOT, 'tickets', ticket['filename'])
        with open(ticket_path, "wb") as f:
            f.write(ticket['ticket'])
        ticket['ticket'] = ticket_path

        with managed(Database()) as db:
            db.add_ticket(ticket)


@app.task
def pack_db():
    """ remove old transaction history """
    with managed(Database()) as db:
        db.pack()