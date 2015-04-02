from __future__ import absolute_import

from celery import Celery
from datetime import timedelta

app = Celery('tasks', broker='amqp://guest@localhost//')

app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'update-every-2-minutes': {
            'task': 'tasks.update_db',
            'schedule': timedelta(120)
        }
    },
)
