import os

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

# Id of the installation
INSTALLATION_ID = get_env_setting('INSTALLATION_ID', 1)

# Access Token to authenticate user to the API
TOKEN = get_env_setting('TOKEN')

# Directory for images
IMAGE_DIR = get_env_setting('IMAGE_DIR', os.path.join(FIGURE_DIR, 'media/images'))
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Directory for snapshots
SNAPSHOT_DIR = get_env_setting('SNAPSHOT_DIR', os.path.join(FIGURE_DIR, 'media/snapshots'))
if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

# Directory for tickets
TICKET_DIR = get_env_setting('TICKET_DIR', 'media/tickets')
if not os.path.exists(TICKET_DIR):
    os.makedirs(TICKET_DIR)

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH', '/usr/local/bin/phantomjs')

# Path to database file
DB_PATH = get_env_setting('DB_FILE', os.path.join(FIGURE_DIR, 'db.fs'))

# Path to ticket CSS
TICKET_CSS_PATH = os.path.join(FIGURE_DIR, 'resources/ticket.css')

# Path to ticket html
TICKET_HTML_PATH = os.path.join(FIGURE_DIR, 'resources/ticket.html')

# Pin used to trigger the process
TRIGGER_PIN = get_env_setting('TRIGGER_PIN', 0)

# ZEO socket adress
ZEO_SOCKET = get_env_setting('ZEO_SOCKET', os.path.join(FIGURE_DIR, 'zeosocket'))

# Timezone information
TIMEZONE = get_env_setting('TIMEZONE', 'Europe/Paris')






