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

# Token to authenticate to the API
TOKEN = get_env_setting('TOKEN')

# User to whom the device is belonging
USER = get_env_setting('FIGURE_USER')

# Root directory for static files
STATIC_ROOT = get_env_setting('STATIC_ROOT', '/Users/benoit/git/figure-raspbian/static')

# Root for media files
MEDIA_ROOT = get_env_setting('MEDIA_ROOT', '/Users/benoit/git/figure-raspbian/media')

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')

# Pin used to trigger the process
TRIGGER_PIN = get_env_setting('TRIGGER_PIN', 0)

# ZEO socket adress
ZEO_SOCKET = get_env_setting('ZEO_SOCKET', os.path.join(FIGURE_DIR, 'zeosocket'))

# Timezone information
TIMEZONE = get_env_setting('TIMEZONE', 'Europe/Paris')

# Countdown for retrying uploading a ticket
RETRY_DELAY = get_env_setting('RETRY_DELAY', 3600)

# Camera model
CAMERA_MODEL = get_env_setting('CAMERA_MODEL', 'UNKNOWN')

# Set rotation of the picture. If ROTATE=1, picture will be rotated 90°
rotate = get_env_setting('CAMERA_TYPE', '0')
ROTATE = True if rotate == '1' else False

# Flash
flash_on = get_env_setting('FLASH_ON', '0')
FLASH_ON = True if flash_on == '1' else False

# Backup
backup_on = get_env_setting('BACKUP_ON', '0')
BACKUP_ON = True if backup_on == '1' else False


def log_config():
    logger.info('ENVIRONMENT: %s' % ENVIRONMENT)
    logger.info('FIGURE_DIR: %s' % FIGURE_DIR)
    logger.info('API_HOST: %s' % API_HOST)
    logger.info('STATIC_ROOT: %s' % STATIC_ROOT)
    logger.info('MEDIA_ROOT: %s' % MEDIA_ROOT)
    logger.info('PHANTOMJS_PATH: %s' % PHANTOMJS_PATH)
    logger.info('TRIGGER_PIN: %s' % TRIGGER_PIN)
    logger.info('ZEO_SOCKET: %s' % TRIGGER_PIN)
    logger.info('TIMEZONE: %s' % TIMEZONE)
    logger.info('RETRY_DELAY: %s' % RETRY_DELAY)
    logger.info('CAMERA_MODEL: %s' % CAMERA_MODEL)
    logger.info('ROTATE: %s' % ROTATE)
    logger.info('FLASH_ON: %s' % FLASH_ON)
    logger.info('BACKUP_ON: %s' % BACKUP_ON)









