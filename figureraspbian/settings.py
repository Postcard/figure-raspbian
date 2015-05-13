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

# Resin IO unique identifier
RESIN_DEVICE_UUID = get_env_setting('RESIN_DEVICE_UUID')

# Environment. Dev if local machine. Prod if Raspberry Pi
ENVIRONMENT = get_env_setting('ENVIRONMENT', 'development')

# Project root
FIGURE_DIR = get_env_setting('FIGURE_DIR', '/Users/benoit/git/figure-raspbian')

# Http host of the API
API_HOST = get_env_setting('API_HOST', 'http://localhost:8000')

# Access Token to authenticate user to the API
TOKEN = get_env_setting('TOKEN')

# Directory for images
IMAGE_DIR = get_env_setting('IMAGE_DIR', os.path.join(FIGURE_DIR, 'media/images'))
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# base URL for images
IMAGE_DIR_URL = get_env_setting('IMAGE_DIR_URL', 'file://%s' % IMAGE_DIR)

# Directory for snapshots
SNAPSHOT_DIR = get_env_setting('SNAPSHOT_DIR', os.path.join(FIGURE_DIR, 'media/snapshots'))
if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

# base URL for snapshots
SNAPSHOT_DIR_URL = get_env_setting('SNAPSHOT_DIR_URL', 'file://%s' % SNAPSHOT_DIR)

# Directory for tickets
TICKET_DIR = get_env_setting('TICKET_DIR', 'media/tickets')
if not os.path.exists(TICKET_DIR):
    os.makedirs(TICKET_DIR)

RESOURCE_DIR = get_env_setting('RESOURCE_DIR', '/Users/benoit/git/figure-raspbian/resources')

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')

# Path to ticket CSS
TICKET_CSS_PATH = os.path.join(RESOURCE_DIR, 'ticket.css')

# Path to ticket html
TICKET_HTML_PATH = os.path.join(RESOURCE_DIR, 'ticket.html')

# URL of ticket.css
TICKET_CSS_URL = get_env_setting('TICKET_CSS_URL', "file://%s" % TICKET_CSS_PATH)

# URL of ticket.html
TICKET_HTML_URL = get_env_setting('TICKET_HTML_URL', "file://%s" % TICKET_HTML_PATH)

# Pin used to trigger the process
TRIGGER_PIN = get_env_setting('TRIGGER_PIN', 0)

# ZEO socket adress
ZEO_SOCKET = get_env_setting('ZEO_SOCKET', os.path.join(FIGURE_DIR, 'zeosocket'))

# Timezone information
TIMEZONE = get_env_setting('TIMEZONE', 'Europe/Paris')

# Countdown for retrying uploading a ticket
RETRY_DELAY = get_env_setting('RETRY_DELAY', 3600)

# Camera type
CAMERA_TYPE = get_env_setting('CAMERA_TYPE', 'CANON')

# Flash
flash_on = get_env_setting('FLASH_ON', '0')
FLASH_ON = True if flash_on == '1' else False

def log_config():
    logger.info('RESIN_DEVICE_UUID: %s' % RESIN_DEVICE_UUID)
    logger.info('ENVIRONMENT: %s' % ENVIRONMENT)
    logger.info('FIGURE_DIR: %s' % FIGURE_DIR)
    logger.info('API_HOST: %s' % API_HOST)
    logger.info('IMAGE_DIR: %s' % IMAGE_DIR)
    logger.info('IMAGE_DIR_URL: %s' % IMAGE_DIR_URL)
    logger.info('SNAPSHOT_DIR: %s' % SNAPSHOT_DIR)
    logger.info('SNAPSHOT_DIR_URL: %s' % SNAPSHOT_DIR_URL)
    logger.info('TICKET_DIR: %s' % TICKET_DIR)
    logger.info('RESOURCE_DIR: %s' % RESOURCE_DIR)
    logger.info('PHANTOMJS_PATH: %s' % PHANTOMJS_PATH)
    logger.info('TICKET_CSS_PATH: %s' % TICKET_CSS_URL)
    logger.info('TICKET_CSS_URL: %s' % TICKET_CSS_URL)
    logger.info('TICKET_HTML_PATH: %s' % TICKET_HTML_URL)
    logger.info('TICKET_HTML_URL: %s' % TICKET_HTML_URL)
    logger.info('TRIGGER_PIN: %s' % TRIGGER_PIN)
    logger.info('ZEO_SOCKET: %s' % TRIGGER_PIN)
    logger.info('TIMEZONE: %s' % TIMEZONE)
    logger.info('RETRY_DELAY: %s' % RETRY_DELAY)
    logger.info('CAMERA_TYPE: %s' % CAMERA_TYPE)
    logger.info('FLASH_ON: %s' % FLASH_ON)









