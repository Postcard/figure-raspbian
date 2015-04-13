# coding=utf-8

import random
import time
import os
from datetime import datetime
import pytz
from string import Template as StringTemplate

from hashids import Hashids
from jinja2 import Environment

from . import settings


FIGURE_TIME_ORIGIN = 1409529600.0


def with_base_html(rendered):
    """
    add html boilerplate to rendered template
    """
    base = """<!doctype html>
            <html class="figure figure-ticket-container">
                <head>
                    <meta charset="utf-8">
                    <link rel="stylesheet" href="file://$ticket_css">
                    </head>
                <body class="figure figure-ticket-container">
                    <div class="figure figure-ticket">
                    $content
                    </div>
                </body>
            </html>
        """
    return StringTemplate(base).substitute(content=rendered, ticket_css=settings.TICKET_CSS_PATH)


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

    def generics(self, installation):
        """
        Calculate generics variables like datetime, code. These variables are not randomly calculated but
        deterministically calculated
        :return:
        """
        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        epoch = int(time.mktime(now.timetuple()) - FIGURE_TIME_ORIGIN)
        hashids = Hashids()
        code = hashids.encode(epoch, int(installation)).upper()
        return now, code

    def render(self, installation, snapshot):
        context = {'snapshot': 'file://%s' % snapshot}
        (random_text_selections, random_image_selections) = self.random_selection()
        for (text_variable_id, item) in random_text_selections:
            context['textvariable_%s' % text_variable_id] = item['text']
        for (image_variable_id, item) in random_image_selections:
            context['imagevariable_%s' % image_variable_id] = 'file://%s/%s' % (settings.IMAGE_DIR,
                                                                                os.path.basename(item['media']))
        now, code = self.generics(installation)
        context['datetime'] = now
        context['code'] = code
        for im in self.images:
            context['image_%s' % im['id']] = 'file://%s/%s' % (settings.IMAGE_DIR, os.path.basename(im['media']))
        template = JINJA_ENV.from_string(self.html)
        html = with_base_html(template.render(context))
        return html, now, code, random_text_selections, random_image_selections





