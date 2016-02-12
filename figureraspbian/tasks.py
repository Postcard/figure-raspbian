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
    CELERY_TIMEZONE='UTC',
    CELERYD_CONCURRENCY=2
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
def upload_portraits():
    """ Upload all portraits that have not been previously updated"""
    with managed(Database()) as db:
        db.upload_portraits()


@app.task
def update_db():
    with managed(Database()) as db:
        db.update_photobooth()

@app.task
def set_paper_level(paper_level):
    try:
        api.set_paper_level(paper_level)
    except RequestException as e:
        logger.exception(e)

@app.task
def upload_portrait(portrait):
    """ Upload a portrait or add to local portrait list"""
    try:
        # try uploading the ticket
        api.create_portrait(portrait)
    except Exception as e:
        logger.error(e)
        # Couldn't upload the portrait, save picture and ticket
        # to filesystem and add the portrait to local db for scheduled upload
        picture_path = join(settings.MEDIA_ROOT, 'snapshots', portrait['filename'])
        with open(picture_path, "wb") as f:
            f.write(portrait['picture'])
        portrait['picture'] = picture_path

        ticket_path = join(settings.MEDIA_ROOT, 'tickets', portrait['filename'])
        with open(ticket_path, "wb") as f:
            f.write(portrait['ticket'])
        portrait['ticket'] = ticket_path

        with managed(Database()) as db:
            db.add_portrait(portrait)


@app.task
def pack_db():
    """ remove old transaction history """
    with managed(Database()) as db:
        db.pack()