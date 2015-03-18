import requests
from requests.exceptions import Timeout, ConnectionError


def internet_on():
    try:
        requests.get('http://74.125.228.100', timeout=1)
        return True
    except Timeout:
        pass
    except ConnectionError:
        pass
    return False

