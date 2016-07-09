# -*- coding: utf8 -*-


import logging

import figure

from . import settings
from .utils import url2name

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

figure.api_base = settings.API_HOST
figure.token = settings.TOKEN





def create_portrait(portrait):

    try:
        files = {'picture_color': open(portrait['picture'], 'rb'), 'ticket': open(portrait['ticket'], 'rb')}
    except Exception as e:
        logger.error(e)
        files = {
            'picture_color': (portrait['filename'], portrait['picture']),
            'ticket': (portrait['filename'], portrait['ticket'])
        }

    data = {
        'taken': portrait['taken'],
        'place': portrait['place'],
        'event': portrait['event'],
        'photobooth': portrait['photobooth'],
        'code': portrait['code'],
        'is_door_open': portrait['is_door_open']
    }

    figure.Portrait.create(data=data, files=files)

