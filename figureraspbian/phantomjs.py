# -*- coding: utf8 -*-

import subprocess

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from . import settings


class PhantomJsException(Exception):
    pass


def save_screenshot(ticket_path):

    args = [settings.PHANTOMJS_PATH, './figureraspbian/ticket.js', ticket_path]
    subprocess.check_output(args)



