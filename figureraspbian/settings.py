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


# Root directory for static files
STATIC_ROOT = get_env_setting('STATIC_ROOT', '/Users/benoit/git/figure-raspbian/static')

# Root for media files
MEDIA_ROOT = get_env_setting('MEDIA_ROOT', '/Users/benoit/git/figure-raspbian/media')

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')

# Pin used to trigger the process
BUTTON_PIN = int(get_env_setting('BUTTON_PIN', 2))

# Number of line feed at the end of the ticket
LINE_FEED_COUNT = int(get_env_setting('LINE_FEED_COUNT', 5))

# Ticket template configuration
TICKET_TEMPLATE_TITLE = u'Émilie et Patrick'
TICKET_TEMPLATE_DESCRIPTION = u'16 juillet 2016'





