# -*- coding: utf8 -*-

import os

import logging
logger = logging.getLogger(__name__)


class ImproperlyConfigured(Exception):
    pass


def get_env_setting(setting, default=None):
    """ Get the environment setting or return exception """
    if setting in os.environ:
        return os.environ[setting]
    elif default is not None:
        return default
    else:
        error_msg = "Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)


DEBUG = get_env_setting('DEBUG', True)

# Http host of the API
API_HOST = get_env_setting('API_HOST', 'http://localhost:8000')

# Http host for static files
STATIC_HOST = get_env_setting('STATIC_HOST', API_HOST)

# Token to authenticate to the API
TOKEN = get_env_setting('TOKEN', 'token')

RESIN_UUID = get_env_setting('RESIN_DEVICE_UUID', 'resin_uuid')

# Root directory to store data
DATA_ROOT = get_env_setting('DATA_ROOT', '/Users/benoit/git/figure-raspbian')

# Root directory for static files
STATIC_ROOT = get_env_setting('STATIC_ROOT', '/Users/benoit/git/figure-raspbian/static')

# Root for media files
MEDIA_ROOT = get_env_setting('MEDIA_ROOT', '/Users/benoit/git/figure-raspbian/media')
IMAGE_ROOT = os.path.join(MEDIA_ROOT, 'images')
PICTURE_ROOT = os.path.join(MEDIA_ROOT, 'pictures')
TICKET_ROOT = os.path.join(MEDIA_ROOT, 'tickets')
MEDIA_URL = 'file://%s' % MEDIA_ROOT

TICKET_CSS_URL = "%s/%s" % (STATIC_HOST, 'static/css/ticket.css')
LOCAL_TICKET_CSS_URL = 'file://%s/ticket.css' % STATIC_ROOT

BOOTING_TICKET_TEMPLATE_URL = "%s/%s" % (STATIC_HOST, 'static/ticket_templates/booting.html')
LOGO_FIGURE_URL = "%s/%s" % (STATIC_HOST, 'static/images/logo_figure.jpg')
LOCAL_LOGO_FIGURE_URL = 'file://%s/logo_figure.jpg' % STATIC_ROOT

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')

# Pin used to trigger the process
BUTTON_PIN = get_env_setting('BUTTON_PIN', 0)

# Timezone information
DEFAULT_TIMEZONE = 'Europe/Paris'

# Camera config
APERTURE = int(get_env_setting('APERTURE', 11))
SHUTTER_SPEED = int(get_env_setting('SHUTTER_SPEED', 39))
ISO = int(get_env_setting('ISO', 3))
CAPTURE_DELAY = float(get_env_setting('CAPTURE_DELAY', 1.0))


# Paper roll length in cm
PAPER_ROLL_LENGTH = int(get_env_setting('PAPER_ROLL_LENGTH', 8000))
PIXEL_CM_RATIO = float(get_env_setting('PIXEL_CM_RATIO', 75.59))

# Number of line feed at the end of the ticket
LINE_FEED_COUNT = int(get_env_setting('LINE_FEED_COUNT', 5))

WIFI_ON = int(get_env_setting('WIFI_ON', 0))

DOOR_OPENING_DELAY = int(get_env_setting('DOOR_OPENING_DELAY', 5))
DOOR_OPENING_TIME = int(get_env_setting('DOOR_OPENING_TIME', 10))


UPDATE_POLL_INTERVAL = int(get_env_setting('UPDATE_POLL_INTERVAL', 90))
UPLOAD_PORTRAITS_INTERVAL = int(get_env_setting('UPLOAD_PORTRAITS_INTERVAL', 90))

LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
