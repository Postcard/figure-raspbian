# -*- coding: utf8 -*-

import os
from os.path import basename, join
import urllib
import time
from urlparse import urlsplit
import random
import cStringIO
import base64
import subprocess
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from PIL import Image
from hashids import Hashids

import settings


def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.unquote(urlsplit(url)[2]))


def weighted_choice(choices):
    """ Weighted random.choice """
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w
    assert False, "Shouldn't get here"


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
    my_env['PNG2POS_PRINTER_MAX_WIDTH'] = '576'

    p = subprocess.Popen(args, stdout=subprocess.PIPE, env=my_env)
    pos_data, err = p.communicate()
    if err:
        raise err
    return pos_data


hashids = Hashids(salt='Titi Vicky Benni')


def get_file_name(installation_id, date):
    unique_id = "{hash}{resin_uuid}".format(
        hash=hashids.encode(installation_id, int(date.strftime('%Y%m%d%H%M%S'))),
        resin_uuid=settings.RESIN_UUID[:4]).lower()
    return "Figure_%s.jpg" % unique_id


def pixels2cm(pixels):
    return float(pixels) / settings.PIXEL_CM_RATIO