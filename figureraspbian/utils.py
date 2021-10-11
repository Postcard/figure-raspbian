# -*- coding: utf8 -*-

import time
import logging
import base64
import io
import netifaces
import re
import subprocess
from os.path import join, basename, exists
import os
from urllib.parse import urlsplit
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import codecs

from hashids import Hashids
from PIL import ImageOps, ImageEnhance
from jinja2 import Environment

from . import settings


logger = logging.getLogger(__name__)
hashids = Hashids(salt='Titi Vicky Benni')


def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.parse.unquote(urlsplit(url)[2]))


def write_file(file, path):
    """ Write a file to a specific path """
    with open(path, "wb") as f:
        f.write(file)


def download(url, path, force=False):
    """
    Download a file from a remote url and copy it to the local path
    """
    local_name = url2name(url)
    path_to_file = join(path, local_name)
    if not exists(path_to_file) or force:
        req = urllib.request.Request(url)
        r = urllib.request.urlopen(req, timeout=10)
        write_file(r.read(), path_to_file)
    return path_to_file


def get_file_name(code):
    # TODO check for unicity
    ascii = [ord(c) for c in code]
    hash = hashids.encode(*ascii)
    return "Figure_%s.jpg" % hash


def timeit(func):

    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time()
        logger.info('%r %2.2f sec' % (func.__name__, te-ts))
        return result
    return timed


def get_data_url(picture):
    buf = io.BytesIO()
    picture.save(buf, picture.format)
    data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    mime_type = 'image/%s' % picture.format.lower()
    data_url = 'data:%s;base64,%s' % (mime_type, data)
    return data_url


def pixels2cm(pixels):
    return float(pixels) / settings.PIXEL_CM_RATIO


def new_paper_level(old_paper_level, ticket_length):
    if old_paper_level == 0:
        return 100.0
    cm = pixels2cm(ticket_length)
    new_paper_level = old_paper_level - (cm / float(settings.PAPER_ROLL_LENGTH)) * 100
    if new_paper_level <= 1:
        # estimate is wrong, guess it's 10%
        new_paper_level = 10
    return new_paper_level


def set_system_time(dt):
    date_format = "%Y-%m-%d %H:%M:%S"
    date_string = dt.strftime(date_format)
    cmd = 'date -s "%s"' % date_string
    os.system(cmd)


def get_mac_addresses():
    mac_addresses = []
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        ifaddresses = netifaces.ifaddresses(interface)
        af_link = ifaddresses.get(netifaces.AF_LINK)
        if af_link and len(af_link) > 0:
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


def get_usb_devices():
    pattern = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<vendor_id>\w+):(?P<product_id>\w+)\s(?P<tag>.+)$", re.I)
    df = subprocess.check_output("lsusb", shell=True).decode('utf-8')
    # parse all usb devices
    devices = []
    for i in df.split('\n'):
        if i:
            info = pattern.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
                devices.append(dinfo)
    return devices


def crop_to_square(pil_image):
    """ convert a rectangle image to a square shape """
    w, h = pil_image.size
    left = (w - h) / 2
    top = 0
    right = w - left
    bottom = h
    cropped = pil_image.crop((left, top, right, bottom))
    return cropped


def resize_preserve_ratio(image, new_height=None, new_width=None):
    if new_height:
        (w, h) = image.size
        if h != new_height:
            new_width = int(new_height * w / float(h))
            resized = image.resize((new_width, new_height))
            return resized
    elif new_width:
        (w, h) = image.size
        if w != new_width:
            new_height = int(new_width * h / float(w))
            resized = image.resize((new_width, new_height))
            return resized
    return image


def add_margin(image, border, color='white'):
    """ add an horizontal margin to the image """
    return ImageOps.expand(image, border, color)


@timeit
def enhance_image(image):
    contraster = ImageEnhance.Contrast(image)
    image = contraster.enhance(settings.CONTRAST_FACTOR)
    sharpener = ImageEnhance.Sharpness(image)
    image = sharpener.enhance(settings.SHARPNESS_FACTOR)
    return image