# -*- coding: utf8 -*-

from os.path import basename
import urllib
from urlparse import urlsplit

from retrying import retry

def url2name(url):
    """
    Convert a file url to its base name
    http://api.figuredevices.com/static/css/ticket.css => ticket.css
    """
    return basename(urllib.unquote(urlsplit(url)[2]))


class PhantomJsException(Exception):
    pass

@retry(stop_max_attempt_number=3, wait_fixed=1000, stop_max_delay=15000)
def save_screenshot_with_retry(driver, file):
    result = driver.save_screenshot(file)
    if not result:
        raise PhantomJsException("Something went terribly wrong during screen capture")
    return result
