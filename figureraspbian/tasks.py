# -*- coding: utf8 -*-

from __future__ import absolute_import

from celery import Celery

from . import api
from .utils import internet_on
from . import settings


app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task(rate_limit='10/m')
def create_ticket(installation, snapshot, ticket, datetime, code, random_text_selections, random_image_selections):
    if internet_on():
        api.create_ticket(installation, snapshot, ticket, datetime, code, random_text_selections,
                          random_image_selections)
    else:
        create_ticket.apply_async(
            (installation, snapshot, ticket, datetime, code, random_text_selections, random_image_selections),
            countdown=settings.RETRY_DELAY)




