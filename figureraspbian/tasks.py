from __future__ import absolute_import

from . import api, settings
from .db import Database, managed
from celery import Celery
from datetime import timedelta

app = Celery('tasks', broker='amqp://guest@localhost//')

app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'update-every-2-minutes': {
            'task': 'figureraspbian.tasks.update_db',
            'schedule': timedelta(120)
        }
    },
)


@app.task
def create_ticket(installation, snapshot, ticket, datetime, code, random_text_selections, random_image_selections):
    # TODO handle writing nested field relation in TicketSerializer in the API
    random_text_selection_ids = []
    for selection in random_text_selections:
        created = api.create_random_text_selection(selection[0], selection[1]['id'])
        random_text_selection_ids.append(created)
    random_image_selection_ids = []
    for selection in random_image_selections:
        created = api.create_random_image_selection(selection[0], selection[1]['id'])
        random_image_selection_ids.append(created)
    api.create_ticket(installation, snapshot, ticket, datetime, code, random_image_selection_ids, random_image_selection_ids)


@app.task
def update_db():
    with managed(Database(settings.ENVIRONMENT)) as db:
        db.update()




