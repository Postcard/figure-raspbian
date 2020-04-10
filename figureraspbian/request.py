# -*- coding: utf8 -*-

import logging
from os import path
from threading import Thread
import errno

import figure
from gpiozero import PingServer

import settings
from models import Photobooth, Portrait, Code
import utils


figure.api_base = settings.API_HOST
figure.token = settings.TOKEN


logger = logging.getLogger(__name__)


def download_ticket_stylesheet():
    utils.download(settings.TICKET_CSS_URL, settings.STATIC_ROOT, force=True)


def download_booting_ticket_template():
    utils.download(settings.LOGO_FIGURE_URL, settings.STATIC_ROOT)
    utils.download(settings.BOOTING_TICKET_TEMPLATE_URL, settings.STATIC_ROOT, force=True)


def update():
    """ This will update the data in case it has been changed in the API """
    photobooth = Photobooth.get()
    # print(settings.RESIN_UUID)
    updated = figure.Photobooth.get(settings.RESIN_UUID)
    # print(updated)
    return photobooth.update_from_api_data(updated)


def upload_portrait(portrait):
    """ Upload a portrait to Figure API or save it to local file system if an error occurs"""

    files = {
        'picture_color': (portrait['filename'], portrait['picture']),
        'ticket': (portrait['filename'], portrait['ticket'])
    }

    data = {key: portrait[key] for key in ['code', 'taken', 'place', 'event', 'photobooth']}

    try:
        logger.info('Uploading portrait %s' % portrait['code'])
        figure.Portrait.create(data=data, files=files)
        logger.info('Portrait %s uploaded !' % portrait['code'])
    except Exception as e:
        logger.error(e)
        # Couldn't upload the portrait, save picture and ticket
        # to filesystem and add the portrait to local db for scheduled upload
        picture_path = path.join(settings.PICTURE_ROOT,  portrait['filename'])
        utils.write_file(portrait['picture'], picture_path)

        ticket_path = path.join(settings.TICKET_ROOT, portrait['filename'])
        utils.write_file(portrait['ticket'], ticket_path)

        portrait['picture'] = picture_path
        portrait['ticket'] = ticket_path
        portrait.pop('filename')

        portrait['place_id'] = portrait.pop('place')
        portrait['event_id'] = portrait.pop('event')
        portrait['photobooth_id'] = portrait.pop('photobooth')

        Portrait.create(**portrait)


def upload_portrait_async(portrait):
    thr = Thread(target=upload_portrait, args=(portrait,), kwargs={})
    thr.start()


def upload_portraits():

    not_uploaded_count = Portrait.not_uploaded_count()

    if not_uploaded_count > 0:

        logger.info('There are %s to be uploaded...' % not_uploaded_count)

        while True:
            portrait = Portrait.first_not_uploaded()
            if portrait:
                logger.info('Uploading portrait %s...' % portrait.code)
                try:
                    files = {'picture_color': open(portrait.picture, 'rb'), 'ticket': open(portrait.ticket, 'rb')}
                    data = {
                        'code': portrait.code,
                        'taken': portrait.taken,
                        'place': portrait.place_id,
                        'event': portrait.event_id,
                        'photobooth': portrait.photobooth_id,
                    }
                    figure.Portrait.create(data=data, files=files)
                    portrait.uploaded = True
                    portrait.save()
                    logger.info('Portrait %s uploaded !' % portrait.code)
                except figure.BadRequestError as e:
                    # Duplicate code or files empty
                    logger.exception(e)
                    portrait.delete_instance()
                except IOError as e:
                    logger.exception(e)
                    if e.errno == errno.ENOENT:
                        # snapshot or ticket file may be corrupted, proceed with remaining tickets
                        portrait.delete_instance()
                    else:
                        break
                except Exception as e:
                    logger.exception(e)
                    break
            else:
                break


def update_paper_level(paper_level):
    figure.Photobooth.edit(
        settings.RESIN_UUID, data={'paper_level': paper_level})
    logger.info('API updated with new paper level!')


def update_paper_level_async(paper_level):
    thr = Thread(target=update_paper_level, args=(paper_level,), kwargs={})
    thr.start()


def update_mac_addresses():
    mac_addresses = utils.get_mac_addresses()
    figure.Photobooth.edit(
        settings.RESIN_UUID, data={'mac_addresses': mac_addresses})


def update_mac_addresses_async():
    thr = Thread(target=update_mac_addresses, args=(), kwargs={})
    thr.start()


def claim_new_codes():
    if Code.less_than_1000_left():
        logger.info('We are running out of codes, fetching new ones from API...')
        new_codes = figure.Code.claim(data={'number': 10000})
        Code.bulk_insert(new_codes)
        logger.info('New codes fetched and saved !')

def is_online():
    # check if the device is online
    ping_host = '8.8.8.8'
    server = PingServer(ping_host)
    b = server.is_active
    server.close()
    return b