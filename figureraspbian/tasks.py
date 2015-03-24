from celery import Celery
from . import api, settings
from .db import Database


app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task
def create_ticket(snapshot, ticket, datetime, code, random_text_selections, random_image_selections):
    # TODO handle writing nested field relation in TicketSerializer in the API
    random_text_selection_ids = []
    for selection in random_text_selections:
        created = api.create_random_text_selection(selection[0], selection[1]['id'])
        random_text_selection_ids.push(created)
    random_image_selection_ids = []
    for selection in random_image_selections:
        created = api.create_random_image_selection(selection[0], selection[1]['id'])
        random_image_selection_ids.push(created)
    api.create_ticket(snapshot, ticket, datetime, code, random_image_selection_ids, random_image_selection_ids)

database = Database(settings.ENVIRONMENT)

@app.task
def update_db():
    database.update()

