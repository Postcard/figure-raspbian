# -*- coding: utf-8 -*-

import os
import random
import settings

from jinja2 import Environment

from utils import timeit

def with_base_html(rendered):
    """
    add html boilerplate to rendered template
    """
    base = u"""<!doctype html>
<html class="figure figure-ticket-container">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="file://{static_root}/ticket.css">
    </head>
    <body class="figure figure-ticket-container">
        <div class="figure figure-ticket">
            {content}
        </div>
    </body>
</html>"""
    return base.format(static_root=settings.STATIC_ROOT, content=rendered)


def datetimeformat(value, format='%Y-%m-%d'):
    """
    Jinja filter used to format date
    :param value:
    :param format:
    :return:
    """
    return value.strftime(format)

JINJA_ENV = Environment()
JINJA_ENV.filters['datetimeformat'] = datetimeformat


def random_selection(variable):
    """
    Randomly select an item from a variable
    :return: a random selection
    """
    if not variable['items']:
        return variable['id'], None
    return variable['id'], random.choice(variable['items'])

@timeit
def render(html, snapshot, code, date, images):
    context = {'snapshot': snapshot, 'datetime': date, 'code': code}
    for im in images:
        image_url = 'file://%s/images/%s' % (settings.MEDIA_ROOT, os.path.basename(im['image']))
        context['image_%s' % im['id']] = image_url
    template = JINJA_ENV.from_string(with_base_html(html))
    rendered_html = template.render(context)
    return rendered_html





