# -*- coding: utf-8 -*-

import random
import os
from datetime import datetime
import pytz

from jinja2 import Environment

from . import settings


FIGURE_TIME_ORIGIN = 1409529600.0


def with_base_html(rendered):
    """
    add html boilerplate to rendered template
    """
    base = u"""<!doctype html>
<html class="figure figure-ticket-container">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="{ticket_css}">
    </head>
    <body class="figure figure-ticket-container">
        <div class="figure figure-ticket">
            {content}
            <br>
            <p style='text-align:center;'>
                <span style='letter-spacing: 0.2em; border: 2px solid #000; padding: 10px 9px 8px 13px; margin-bottom: 16px; margin-left: 8px; display: inline-block;'>{{{{code}}}}</span>
                <br/>
                <small>Tapez votre code sur<br/>figuredevices.com</small>
            </p>
        </div>
    </body>
</html>"""
    return base.format(content=rendered, ticket_css=settings.TICKET_CSS_URL)



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


class TicketRenderer(object):

    def __init__(self, html, text_variables, image_variables, images):
        """
        :param template_html: Jinja template HTML + CSS
        :param text_variables: an array of text variables {id: "5689", items: ["un peu", "beaucoup", "à la folie"]}
        :param image_variables: an array of image variables {id: "5690", items: ["media_url_1", "media_url-2", "media_url_3"]}
        :param images: an array of images {id: "5896", media_url: "media_url"}
        :return:
        """
        self.html = html
        self.text_variables = text_variables
        self.image_variables = image_variables
        self.images = images

    def random_selection(self):
        """
        Randomly selects variables items
        :return: a random selection
        """
        random_text_selections = [(text_variable['id'], random.choice(text_variable['items'])) for
                                  text_variable in self.text_variables if len(text_variable['items']) > 0]

        random_image_selections = [(image_variable['id'], random.choice(image_variable['items'])) for
                                   image_variable in self.image_variables if len(image_variable['items']) > 0]
        return random_text_selections, random_image_selections

    def render(self, snapshot, code):
        context = {'snapshot': '%s/%s' % (settings.SNAPSHOT_DIR_URL, os.path.basename(snapshot))}
        (random_text_selections, random_image_selections) = self.random_selection()
        for (text_variable_id, item) in random_text_selections:
             context['textvariable_%s' % text_variable_id] = item['text']
        for (image_variable_id, item) in random_image_selections:
            context['imagevariable_%s' % image_variable_id] = '%s/%s' % (settings.IMAGE_DIR_URL,
                                                                         os.path.basename(item['image']))
        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        context['datetime'] = now
        context['code'] = code
        for im in self.images:
            context['image_%s' % im['id']] = '%s/%s' % (settings.IMAGE_DIR_URL, os.path.basename(im['image']))
        template = JINJA_ENV.from_string(with_base_html(self.html))
        rendered_html = template.render(context)
        return rendered_html, now, code, random_text_selections, random_image_selections





