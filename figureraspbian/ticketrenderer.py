# coding=utf-8

import random
import time
from datetime import datetime
from hashids import Hashids
from jinja2 import Environment


FIGURE_TIME_ORIGIN = 1409529600.0


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
        variables = []
        variables.extend(self.text_variables)
        variables.extend(self.image_variables)
        random_selection = {}
        for variable in variables:
            variable_id = 'variable_%s' % variable['id']
            random_selection[variable_id] = random.choice(variable['items'])
        return random_selection

    def generics(self):
        """
        Calculate generics variables like datetime, code. These variables are not randomly calculated but
        deterministically calculated
        :return:
        """
        now = datetime.now()
        epoch = int(time.mktime(now.timetuple()) - FIGURE_TIME_ORIGIN)
        hashids = Hashids()
        code = hashids.encode(epoch, int(self.installation)).upper()
        return {'datetime': now, 'code': code}

    def render(self, snapshot):
        context = {'snapshot': snapshot}
        context.update(self.random_selection())
        context.update(self.generics())
        for im in self.images:
            image_id = 'image_%s' % im['id']
            context[image_id] = im['media_url']
            template = JINJA_ENV.from_string(self.html)
        return template.render(context)





