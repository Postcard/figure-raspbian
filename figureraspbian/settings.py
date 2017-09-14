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


########## API CONFIGURATION
# Http host of the API
API_HOST = get_env_setting('API_HOST', 'http://localhost:8000')
# Token to authenticate to the API
TOKEN = get_env_setting('TOKEN', 'token')
RESIN_UUID = get_env_setting('RESIN_DEVICE_UUID', 'resin_uuid')
UPDATE_POLL_INTERVAL = int(get_env_setting('UPDATE_POLL_INTERVAL', 90))
UPLOAD_PORTRAITS_INTERVAL = int(get_env_setting('UPLOAD_PORTRAITS_INTERVAL', 90))
CLAIM_NEW_CODES_INTERVAL = int(get_env_setting('CLAIM_NEW_CODES_INTERVAL', 3600))
NUMBER_OF_CODES_TO_CLAIM = int(get_env_setting('NUMBER_OF_CODES_TO_CLAIM', 5000))
# Timezone information
DEFAULT_TIMEZONE = 'Europe/Paris'
########## END API CONFIGURATION

########## SQLITE CONFIGURATION
# Root directory to store data
SQLITE_FILEPATH = get_env_setting('SQLITE_FILEPATH', ':memory:')
########## SQLITE CONFIGURATION

######### STATIC FILES CONFIGURATION
# Http host for static files
STATIC_HOST = get_env_setting('STATIC_HOST', API_HOST)
TICKET_CSS_URL = "%s/%s" % (STATIC_HOST, 'static/css/ticket.css')
LOGO_FIGURE_URL = "%s/%s" % (STATIC_HOST, 'static/images/logo_figure.jpg')
BOOTING_TICKET_TEMPLATE_URL = "%s/%s" % (STATIC_HOST, 'static/ticket_templates/booting.html')
# Root directory for static files
STATIC_ROOT = get_env_setting('STATIC_ROOT', '/Users/benoit/git/figure-raspbian/static')
LOCAL_TICKET_CSS_URL = 'file://%s/ticket.css' % STATIC_ROOT
LOCAL_LOGO_FIGURE_URL = 'file://%s/logo_figure.jpg' % STATIC_ROOT
######### END STATIC FILES CONFIGURATION

######### MEDIA CONFIGURATION
MEDIA_ROOT = get_env_setting('MEDIA_ROOT', '/Users/benoit/git/figure-raspbian/media')
IMAGE_ROOT = os.path.join(MEDIA_ROOT, 'images')
PICTURE_ROOT = os.path.join(MEDIA_ROOT, 'pictures')
TICKET_ROOT = os.path.join(MEDIA_ROOT, 'tickets')
MEDIA_URL = 'file://%s' % MEDIA_ROOT
RAMDISK_ROOT = get_env_setting('RAMDISK_ROOT', '/mnt/ramdisk')
######### END MEDIA CONFIGURATION

######### PHANTOMJS CONFIGURATION
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')
######### END PHANTOMJS CONFIGURATION

######### I/O CONFIGURATION
IO_INTERFACE = get_env_setting('IO_INTERFACE', 'GPIOZERO')
# Pin used to trigger the process
BUTTON_PIN = int(get_env_setting('BUTTON_PIN', 4))
REMOTE_RELEASE_CONNECTOR_PIN = int(get_env_setting('REMOTE_RELEASE_CONNECTOR_PIN', 5))
DOOR_LOCK_PIN = int(get_env_setting('DOOR_LOCK_PIN', 12))
SHUTDOWN_PIN = int(get_env_setting('SHUTDOWN_PIN', 19))
######### END I/O CONFIGURATION

######### CAMERA CONFIGURATION
APERTURE = int(get_env_setting('APERTURE', 11))
SHUTTER_SPEED = int(get_env_setting('SHUTTER_SPEED', 39))
ISO = int(get_env_setting('ISO', 3))
WHITE_BALANCE = int(get_env_setting('WHITE_BALANCE', 6))
CAPTURE_DELAY = float(get_env_setting('CAPTURE_DELAY', 1.0))
CAMERA_TRIGGER_TYPE = get_env_setting('CAMERA_TRIGGER_TYPE', 'GPHOTO2')
CAMERA_FOCUS_STEPS = int(get_env_setting('CAMERA_FOCUS_STEPS', 20))
######### END CAMERA CONFIGURATION

######## TICKET TEMPLATE CONFIGURATION
TICKET_TEMPLATE_PICTURE_SIZE = int(get_env_setting('TICKET_TEMPLATE_PICTURE_SIZE', 576))
######## END TICKET TEMPLATE CONFIGURATION

######### IMAGE ENHANCEMENT CONFIGURATION
# http://effbot.org/imagingbook/imageenhance.htm
CONTRAST_FACTOR = float(get_env_setting('CONTRAST_FACTOR', 1.0))
SHARPNESS_FACTOR = float(get_env_setting('SHARPNESS_FACTOR', 1.0))
######### END IMAGE ENHANCEMENT CONFIGURATION

######### PRINTER CONFIGURATION
PRINTER_SPEED = int(get_env_setting('PRINTER_SPEED', 2))
PRINTER_MAX_WIDTH = int(get_env_setting('PRINTER_MAX_WIDTH', 576))
# Paper roll length in cm
PAPER_ROLL_LENGTH = int(get_env_setting('PAPER_ROLL_LENGTH', 8000))
PIXEL_CM_RATIO = float(get_env_setting('PIXEL_CM_RATIO', 75.59))
# Number of line feed at the end of the ticket
LINE_FEED_COUNT = int(get_env_setting('LINE_FEED_COUNT', 5))
######### END PRINTER CONFIGURATION

######### DOOR LOCK CONFIGURATION
DOOR_OPENING_DELAY = int(get_env_setting('DOOR_OPENING_DELAY', 5))
DOOR_OPENING_TIME = int(get_env_setting('DOOR_OPENING_TIME', 10))
######## END DOOR LOCK CONFIGURATION

######## RTC CONFIGURATION
RTC = get_env_setting('RTC', '')
RTC_SCLK_PIN = int(get_env_setting('RTC_SLCK_PIN', 3))
RTC_SDAT_PIN = int(get_env_setting('RTC_SDAT_PIN', 2))
RTC_RST_PIN = int(get_env_setting('RTC_RST_PIN', 13))
######## END RTC CONFIGURATION

######## WIFI CONFIGURATION
WIFI_ON = int(get_env_setting('WIFI_ON', 0))
######## END WIFI CONFIGURATION

######## SHUTDOWN CONFIGURATION
SHUTDOWN_HOOK_ON = int(get_env_setting('SHUTDOWN_HOOK_ON', 0))
######## END SHUTDOWN CONFIGURATION

####### SERVER CONFIGURATION
SERVER_ON = int(get_env_setting('SERVER_ON', 0))
####### END SERVER CONFIGURATION

######## LOG CONFIGURATION
LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
######## END LOG CONFIGURATION

######## RESINIO SUPERVISOR CONFIGURATION
RESIN_SUPERVISOR_ADDRESS = get_env_setting('RESIN_SUPERVISOR_ADDRESS', '')
RESIN_SUPERVISOR_API_KEY = get_env_setting('RESIN_SUPERVISOR_API_KEY', '')
RESIN_APP_ID = get_env_setting('RESIN_APP_ID', '')
######## END RESINIO SUPERVISOR CONFIGURATION

