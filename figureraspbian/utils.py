# -*- coding: utf8 -*-

import os
from os.path import basename, exists
import urllib
import logging
import time

from urlparse import urlsplit
import cStringIO
import base64
import subprocess
import urllib2
from os.path import join

from PIL import Image
from hashids import Hashids

from figureraspbian import settings


logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.unquote(urlsplit(url)[2]))


def download(url, path):
    """
    Download a file from a remote url and copy it to the local path
    """
    local_name = url2name(url)
    path_to_file = join(path, local_name)
    if not exists(path_to_file):
        req = urllib2.Request(url)
        r = urllib2.urlopen(req, timeout=10)
        write_file(r.read(), path_to_file)
    return path_to_file


def write_file(file, path):
    """
    Write a file to a specific path
    """
    with open(path, "wb") as f:
        f.write(file)


def read_file(path):
    """
    Open a file and return its content
    """
    with open(path, 'rb') as content_file:
        content = content_file.read()
    return content


def timeit(func):

    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time()
        logger.info('%r %2.2f sec' % (func.__name__, te-ts))
        return result
    return timed


@timeit
def get_base64_picture_thumbnail(picture):
    buf = cStringIO.StringIO()
    picture.resize((576, 576)).save(buf, "JPEG")
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


def get_file_name(code):
    # TODO check for unicity
    ascii = [ord(c) for c in code]
    hash = hashids.encode(*ascii)
    return "Figure_%s.jpg" % hash


def pixels2cm(pixels):
    return float(pixels) / settings.PIXEL_CM_RATIO





