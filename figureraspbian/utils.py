# -*- coding: utf8 -*-

import os
from os.path import join
import time
import cStringIO
import base64
import subprocess
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)
from datetime import datetime
import random

from PIL import Image
from hashids import Hashids

import settings


def timeit(func):

    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time()
        logger.info('%r %2.2f sec' % (func.__name__, te-ts))
        return result
    return timed

@timeit
def get_base64_snapshot_thumbnail(snapshot):
    buf = cStringIO.StringIO()
    snapshot.resize((512, 512)).save(buf, "JPEG")
    content = base64.b64encode(buf.getvalue())
    buf.close()
    return content

@timeit
def get_pure_black_and_white_ticket(ticket_io):
    ticket = Image.open(cStringIO.StringIO(ticket_io))
    ticket = ticket.convert('1')
    ticket_path = join(settings.MEDIA_ROOT, 'ticket.png')
    ticket.save(ticket_path, ticket.format, quality=100)
    _, ticket_length = ticket.size
    return ticket_path, ticket_length

@timeit
def png2pos(path):
    # TODO make png2pos support passing base64 file argument
    args = ['png2pos', '-r', '-s2', '-aC', path]
    my_env = os.environ.copy()
    my_env['PNG2POS_PRINTER_MAX_WIDTH'] = '512'

    p = subprocess.Popen(args, stdout=subprocess.PIPE, env=my_env)
    pos_data, err = p.communicate()
    if err:
        raise err
    return pos_data


hashids = Hashids(salt='Titi Vicky Benni')

def get_file_name(count):
    now = datetime.now()
    hash = hashids.encode(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second,
        count,
        random.randint(0, 100))
    return "Figure_%s.jpg" % hash

