# -*- coding: utf8 -*-
from os.path import join

import subprocess

from figureraspbian import settings
from figureraspbian.utils import timeit

@timeit
def get_screenshot(html):
    file_path = join(settings.RAMDISK_ROOT, 'ticket.html')
    with open(file_path, 'wb') as f:
        f.write(html)
    file_url = 'file://%s' % file_path
    output_path = join(settings.RAMDISK_ROOT, 'ticket.png')
    args = ['webkit2png', '--xvfb', '1024', '768', '--output', output_path, file_url]
    subprocess.check_output(args)
    with open(output_path, 'rb') as ticket:
        return ticket.read()


