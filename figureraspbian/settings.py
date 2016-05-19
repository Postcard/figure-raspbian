# -*- coding: utf8 -*-

import os

import logging
logging.basicConfig(level='INFO')
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


# Environment. Dev if local machine. Prod if Raspberry Pi
ENVIRONMENT = get_env_setting('ENVIRONMENT', 'development')

# Project root
FIGURE_DIR = get_env_setting('FIGURE_DIR', '/Users/benoit/git/figure-raspbian')

# Http host of the API
API_HOST = get_env_setting('API_HOST', 'http://localhost:8000')

# Http host for static files
STATIC_HOST = get_env_setting('STATIC_HOST', API_HOST)

# Token to authenticate to the API
TOKEN = get_env_setting('TOKEN', 'token')

# User to whom the device is belonging
USER = get_env_setting('FIGURE_USER', '1')

RESIN_UUID = get_env_setting('RESIN_DEVICE_UUID', 'resin_uuid')

# Root directory to store data
DATA_ROOT = get_env_setting('DATA_ROOT', '/Users/benoit/git/figure-raspbian')

# Root directory for static files
STATIC_ROOT = get_env_setting('STATIC_ROOT', '/Users/benoit/git/figure-raspbian/static')

# Root for media files
MEDIA_ROOT = get_env_setting('MEDIA_ROOT', '/Users/benoit/git/figure-raspbian/media')

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')

# Pin used to trigger the process
TRIGGER_PIN = get_env_setting('TRIGGER_PIN', 0)

# Pin used for the relay
OUTPUT_PIN = get_env_setting('OUTPUT_PIN', 0)

# ZEO socket adress
ZEO_SOCKET = get_env_setting('ZEO_SOCKET', os.path.join(DATA_ROOT, 'zeo.sock'))

# Timezone information
DEFAULT_TIMEZONE = 'Europe/Paris'

# Camera config
APERTURE = int(get_env_setting('APERTURE', 11))
SHUTTER_SPEED = int(get_env_setting('SHUTTER_SPEED', 39))
ISO = int(get_env_setting('ISO', 3))
CAPTURE_DELAY = float(get_env_setting('CAPTURE_DELAY', 1.0))

# Input configuration
INPUT_LOW = int(get_env_setting('INPUT_LOW', 0))
INPUT_HIGH = 0 if INPUT_LOW else 1

# Paper roll length in cm
PAPER_ROLL_LENGTH = int(get_env_setting('PAPER_ROLL_LENGTH', 8000))
PIXEL_CM_RATIO = float(get_env_setting('PIXEL_CM_RATIO', 75.59))

# Number of line feed at the end of the ticket
LINE_FEED_COUNT = int(get_env_setting('LINE_FEED_COUNT', 5))

WIFI_ON = int(get_env_setting('WIFI_ON', 0))





