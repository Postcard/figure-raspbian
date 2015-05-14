# -*- coding: utf8 -*-


from os.path import join

from selenium import webdriver
from retrying import retry
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from . import settings


class PhantomJsException(Exception):
    pass

@retry(stop_max_attempt_number=3, wait_fixed=1000, stop_max_delay=15000)
def save_screenshot_with_retry(driver, file):
    result = driver.save_screenshot(file)
    if not result:
        logger.info("Phantomjs failed: retrying...")
        raise PhantomJsException("Something went terribly wrong during screen capture")
    return result


def save_screenshot(file_name):
    driver = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)
    ticket_url = 'http://localhost:8080/resources/ticket.html'
    driver.get(ticket_url)
    ticket_path = join(settings.MEDIA_ROOT, 'tickets', file_name)
    save_screenshot_with_retry(driver, ticket_path)
    driver.quit()
    return ticket_path
