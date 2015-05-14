# -*- coding: utf8 -*-


from os.path import join

from selenium import webdriver
import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

from . import settings


class PhantomJsException(Exception):
    pass


def save_screenshot(file_name):
    driver = webdriver.PhantomJS(executable_path=settings.PHANTOMJS_PATH)
    ticket_url = 'http://localhost:8080/resources/ticket.html'
    driver.get(ticket_url)
    ticket_path = join(settings.MEDIA_ROOT, 'tickets', file_name)
    result = driver.save_screenshot(ticket_path)
    driver.quit()
    if not result:
        logger.info("Phantomjs failed: retrying...")
        raise PhantomJsException("Something went terribly wrong during screen capture")
    return ticket_path
