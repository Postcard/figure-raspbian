from celery import Celery
from . import api
from .db import db_proxy

app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task
def create_ticket(*args, **kwargs):
    api.create_ticket(args, kwargs)

@app.task
def update_db():
    db_proxy.update()