import os

class ImproperlyConfigured(Exception):
    pass

def get_env_setting(setting):
    """ Get the environment setting or return exception """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = "Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)


# Http host of the API
API_HOST = get_env_setting('API_HOST')

# Id of the installation
INSTALLATION = get_env_setting('INSTALLATION')

# Access Token to authenticate user to the API
TOKEN = get_env_setting('TOKEN')

# Directory for snapshots
SNAPSHOT_DIR = get_env_setting('SNAPSHOT_DIR')

# Ticket file path
TICKET = get_env_setting('TICKET')

# Path to PhantomJS executable
PHANTOMJS_PATH = get_env_setting('PHANTOMJS_PATH')

# Path to database file
DB_PATH = get_env_setting('DB_FILE')







