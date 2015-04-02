from . import api, settings
from .db import Database, managed
from .celery import app


@app.task
def create_ticket(snapshot, ticket, datetime, code, random_text_selections, random_image_selections):
    # TODO handle writing nested field relation in TicketSerializer in the API
    random_text_selection_ids = []
    for selection in random_text_selections:
        created = api.create_random_text_selection(selection[0], selection[1]['id'])
        random_text_selection_ids.append(created)
    random_image_selection_ids = []
    for selection in random_image_selections:
        created = api.create_random_image_selection(selection[0], selection[1]['id'])
        random_image_selection_ids.append(created)
    api.create_ticket(snapshot, ticket, datetime, code, random_image_selection_ids, random_image_selection_ids)


@app.task
def update_db():
    with managed(Database(settings.ENVIRONMENT)) as db:
        db.update()




