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
import codecs
import io

from PIL import Image
from hashids import Hashids
from jinja2 import Environment
import netifaces
import piexif

from figureraspbian import settings

logging.basicConfig(format=settings.LOG_FORMAT, datefmt='%Y.%m.%d %H:%M:%S', level='INFO')
logger = logging.getLogger(__name__)


def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.unquote(urlsplit(url)[2]))


def download(url, path, force=False):
    """
    Download a file from a remote url and copy it to the local path
    """
    local_name = url2name(url)
    path_to_file = join(path, local_name)
    if not exists(path_to_file) or force:
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
    return open(path, 'rb')


def timeit(func):

    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time()
        logger.info('%r %2.2f sec' % (func.__name__, te-ts))
        return result
    return timed


def crop_to_square(image_data):
    """ convert a rectangle picture to a square shape """
    picture = Image.open(io.BytesIO(image_data))
    exif_dict = piexif.load(picture.info["exif"])
    w, h = picture.size
    left = (w - h) / 2
    top = 0
    right = w - left
    bottom = h
    picture = picture.crop((left, top, right, bottom))
    w, h = picture.size
    exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = w
    exif_bytes = piexif.dump(exif_dict)
    return picture, exif_bytes


@timeit
def get_base64_picture_thumbnail(picture):
    buf = cStringIO.StringIO()
    x = settings.PRINTER_MAX_WIDTH
    picture.resize((x, x)).save(buf, "JPEG")
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
    speed_arg = '-s%s' % settings.PRINTER_SPEED
    args = ['png2pos', '-r', speed_arg, '-aC', path]
    my_env = os.environ.copy()
    my_env['PNG2POS_PRINTER_MAX_WIDTH'] = str(settings.PRINTER_MAX_WIDTH)

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


def get_mac_addresses():
    mac_addresses = []
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        af_link = netifaces.ifaddresses(interface).get(netifaces.AF_LINK)
        if af_link and len(af_link)>0:
            addr = af_link[0].get('addr')
            if addr:
                mac_address = '%s=%s' % (interface, addr)
                mac_addresses.append(mac_address)
    return ','.join(mac_addresses)


def render_jinja_template(path, **kwargs):
    env = Environment()
    with codecs.open(path, 'rb', encoding='utf-8') as content_file:
        template = env.from_string(content_file.read())
        return template.render(kwargs)







