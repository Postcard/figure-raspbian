# -*- coding: utf8 -*-

import subprocess

from figureraspbian import settings
from figureraspbian.utils import timeit


@timeit
def get_screenshot(html):
    args = [settings.PHANTOMJS_PATH, './figureraspbian/ticket.js', html]
    data = subprocess.check_output(args)
    return data



