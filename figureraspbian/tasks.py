# -*- coding: utf8 -*-

from __future__ import absolute_import

from celery import Celery

from . import api
from .utils import internet_on
from . import settings


app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task(rate_limit='10/m')
def upload_tickets():
    with managed(Database()) as db:
    if internet_on():
        while
    else:





