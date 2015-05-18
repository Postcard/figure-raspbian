# -*- coding: utf8 -*-

import subprocess

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from . import settings


class PhantomJsException(Exception):
    pass


def get_screenshot():
    args = [settings.PHANTOMJS_PATH, './figureraspbian/ticket.js']
    data = subprocess.check_output(args)
    return data



