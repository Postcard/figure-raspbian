# -*- coding: utf8 -*-

import subprocess

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from . import settings
from .utils import timeit


@timeit
def get_screenshot(html):
    args = [settings.PHANTOMJS_PATH, './figureraspbian/ticket.js', html]
    data = subprocess.check_output(args)
    return data



