# coding=utf-8

import random
import time
from datetime import datetime
import pytz
from hashids import Hashids
from jinja2 import Environment
from . import settings
from string import Template as StringTemplate


FIGURE_TIME_ORIGIN = 1409529600.0


def with_base_html(rendered):
    """
    add html boilerplate to rendered template
    """
    base = """<!doctype html>
            <html>
                <head>
                    <meta charset="utf-8">
                    <link rel="stylesheet" href="file:///%s">
                    </head>
                <body>
                    <div class="figure figure-ticket">
                    $content
                    </div>
                </body>
            </html>
        """
    return StringTemplate(base).substitute(content=rendered)


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

    def __init__(self, installation, html, text_variables, image_variables, images):
        """
        :param template_html: Jinja template HTML + CSS
        :param text_variables: an array of text variables {id: "5689", items: ["un peu", "beaucoup", "à la folie"]}
        :param image_variables: an array of image variables {id: "5690", items: ["media_url_1", "media_url-2", "media_url_3"]}
        :param images: an array of images {id: "5896", media_url: "media_url"}
        :return:
        """
        self.installation = installation
        self.html = html
        self.text_variables = text_variables
        self.image_variables = image_variables
        self.images = images

    def random_selection(self):
        """
        Randomly selects variables items
        :return: a random selection
        """
        random_text_selections = []
        random_image_selections = []
        for text_variable in self.text_variables:
            selection = (text_variable['id'], random.choice(text_variable['items']))
            random_text_selections.append(selection)
        for image_variable in self.image_variables:
            selection = (image_variable['id'], random.choice(image_variable['items']))
            random_image_selections.append(selection)
        return random_text_selections, random_image_selections

    def generics(self):
        """
        Calculate generics variables like datetime, code. These variables are not randomly calculated but
        deterministically calculated
        :return:
        """
        now = datetime.now(pytz.timezone(settings.TIMEZONE))
        epoch = int(time.mktime(now.timetuple()) - FIGURE_TIME_ORIGIN)
        hashids = Hashids()
        code = hashids.encode(epoch, int(self.installation)).upper()
        return now, code

    def render(self, snapshot):
        context = {'snapshot': snapshot}
        (random_text_selections, random_image_selections) = self.random_selection()
        for (text_variable_id, item) in random_text_selections:
            context['textvariable_%s' % text_variable_id] = item
        for (image_variable_id, item) in random_image_selections:
            context['imagevariable_%s' % image_variable_id] = item
        now, code = self.generics()
        context['datetime'] = now
        context['code'] = code
        for im in self.images:
            context['image_%s' % im['id']] = im['media_url']
        template = JINJA_ENV.from_string(self.html)
        html = with_base_html(template.render(context))
        return html, now, code, random_text_selections, random_image_selections





