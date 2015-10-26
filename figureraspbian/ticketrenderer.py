# -*- coding: utf-8 -*-

import os
import random

from jinja2 import Environment


def with_base_html(rendered):
    """
    add html boilerplate to rendered template
    """
    base = u"""<!doctype html>
<html class="figure figure-ticket-container">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="http://localhost:8080/resources/ticket.css">
    </head>
    <body class="figure figure-ticket-container">
        <div class="figure figure-ticket">
            {content}
        </div>
    </body>
</html>"""
    return base.format(content=rendered)


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


def render(html, snapshot, code, date, images, random_text_selections, random_image_selections):
    context = {'snapshot': snapshot}
    for (text_variable_id, item) in random_text_selections:
        text = item['text'] if item else ''
        context['textvariable_%s' % text_variable_id] = text
    for (image_variable_id, item) in random_image_selections:
        image_url = 'http://localhost:8080/media/images/%s' % os.path.basename(item['image']) if item else ''
        context['imagevariable_%s' % image_variable_id] = image_url
    context['datetime'] = date
    context['code'] = code
    for im in images:
        image_url = 'http://localhost:8080/media/images/%s' % os.path.basename(im['image'])
        context['image_%s' % im['id']] = image_url
    template = JINJA_ENV.from_string(with_base_html(html))
    rendered_html = template.render(context)
    return rendered_html





