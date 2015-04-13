# -*- coding: utf8 -*-

from __future__ import absolute_import

from celery import Celery

from . import api
from .utils import internet_on
from . import settings


app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task(rate_limit='30/m')
def create_ticket(installation, snapshot, ticket, datetime, code, random_text_selections, random_image_selections):
    if internet_on():
        # TODO handle writing nested field relation in TicketSerializer in the API
        random_text_selection_ids = []
        for selection in random_text_selections:
            created = api.create_random_text_selection(selection[0], selection[1]['id'])
            random_text_selection_ids.append(created)
        random_image_selection_ids = []
        for selection in random_image_selections:
            created = api.create_random_image_selection(selection[0], selection[1]['id'])
            random_image_selection_ids.append(created)
        api.create_ticket(installation, snapshot, ticket, datetime, code, random_image_selection_ids,
                          random_image_selection_ids)
    else:
        create_ticket.apply_async(
            (installation, snapshot, ticket, datetime, code, random_text_selections, random_image_selections),
            countdown=settings.RETRY_DELAY)




