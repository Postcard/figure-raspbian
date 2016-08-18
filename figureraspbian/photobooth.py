# -*- coding: utf8 -*-
from threading import Thread, RLock
from datetime import datetime
import pytz
import cStringIO
import base64
import logging
import time
from os.path import join
import errno

from ticketrenderer import TicketRenderer
import figure
from gpiozero import PingServer

from figureraspbian import settings
from figureraspbian.devices.camera import DSLRCamera
from figureraspbian.devices.printer import EpsonPrinter
from figureraspbian.devices.door_lock import PiFaceDigitalDoorLock
from figureraspbian.utils import get_base64_picture_thumbnail, get_pure_black_and_white_ticket, \
    png2pos, get_file_name, download, write_file, read_file, get_mac_addresses, render_jinja_template
from figureraspbian.decorators import execute_if_not_busy
from figureraspbian.phantomjs import get_screenshot
from figureraspbian import db
from figureraspbian.threads import Interval
from figureraspbian.exceptions import DevicesBusy, OutOfPaperError


logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

figure.api_base = settings.API_HOST
figure.token = settings.TOKEN

camera = None
printer = None
button = None
door_lock = None

lock = RLock()


def initialize():
    """
    Initialize devices, data and stylesheets
    """
    # Disable logs for request library
    logging.getLogger("requests").setLevel(logging.WARNING)

    try:
        initialize_devices()
    except Exception as e:
        logger.exception(e)

    if is_online():
        try:
            download_ticket_stylesheet()
        except Exception as e:
            logger.exception(e)

        try:
            download_booting_ticket_template()
        except Exception as e:
            logger.exception(e)

        # update photobooth
        try:
            update()
        except Exception as e:
            logger.exception(e)

        # grab new codes if necessary
        try:
            claim_new_codes()
        except Exception as e:
            logger.exception(e)

        # update mac addresses
        update_mac_addresses_async()


def set_intervals():
    """
    Start tasks that are run in the background at regular intervals
    """

    intervals = [
        Interval(update, settings.UPDATE_POLL_INTERVAL),
        Interval(upload_portraits, settings.UPLOAD_PORTRAITS_INTERVAL)
    ]

    for interval in intervals:
        interval.start()

    return intervals


def initialize_devices():
    global camera, printer, button, door_lock
    camera = DSLRCamera()
    printer = EpsonPrinter()
    door_lock = PiFaceDigitalDoorLock()


def download_ticket_stylesheet():
    download(settings.TICKET_CSS_URL, settings.STATIC_ROOT, force=True)


def download_booting_ticket_template():
    download(settings.LOGO_FIGURE_URL, settings.STATIC_ROOT)
    download(settings.BOOTING_TICKET_TEMPLATE_URL, settings.STATIC_ROOT, force=True)


def door_open():
    door_lock.open()
    time.sleep(settings.DOOR_OPENING_TIME)
    door_lock.close()


def trigger():
    try:
        _trigger()
    except DevicesBusy:
        pass

@execute_if_not_busy(lock)
def _trigger():
    """
    Execute a sequence of actions on devices after a trigger occurs
    Eg:
    - take a photo
    - render a ticket
    - print a ticket
    - upload files
    - etc
    :return:
    """

    picture, exif_bytes = camera.capture()
    return render_print_and_upload(picture, exif_bytes)

@execute_if_not_busy(lock)
def render_print_and_upload(picture, exif_bytes):
    """
    The body of this function is not included in the _trigger function above because we want to print tickets
    with user provided picture. See figureraspbian.api.test_template
    """
    photobooth = db.get_photobooth()

    ticket_renderer = TicketRenderer(
        photobooth.ticket_template.serialize(), settings.MEDIA_URL, settings.LOCAL_TICKET_CSS_URL)

    code = db.get_code()
    tz = photobooth.place.tz if photobooth.place else settings.DEFAULT_TIMEZONE
    date = datetime.now(pytz.timezone(tz))
    base64_picture_thumb = get_base64_picture_thumbnail(picture)

    rendered = ticket_renderer.render(
        picture="data:image/jpeg;base64,%s" % base64_picture_thumb,
        code=code,
        date=date,
        counter=photobooth.counter
    )

    del base64_picture_thumb

    ticket_base64 = get_screenshot(rendered)
    ticket_io = base64.b64decode(ticket_base64)
    ticket_path, ticket_length = get_pure_black_and_white_ticket(ticket_io)

    pos_data = png2pos(ticket_path)

    try:
        printer.print_ticket(pos_data)
        update_paper_level_async(ticket_length)
    except OutOfPaperError:
        update_paper_level_async(0)
    buf = cStringIO.StringIO()
    picture.save(buf, "JPEG", exif=exif_bytes)
    picture_io = buf.getvalue()
    buf.close()

    filename = get_file_name(code)

    portrait = {
        'picture': picture_io,
        'ticket': ticket_io,
        'taken': date,
        'place': photobooth.place.id if photobooth.place else None,
        'event': photobooth.event.id if photobooth.event else None,
        'photobooth': photobooth.id,
        'code': code,
        'filename': filename
    }

    db.increment_counter()
    claim_new_codes_async()
    upload_portrait_async(portrait)

    return ticket_path

@execute_if_not_busy(lock)
def print_booting_ticket():
    booting_template_path = join(settings.STATIC_ROOT, 'booting.html')
    _photobooth = db.get_photobooth()
    tz = _photobooth.place.tz if _photobooth.place else settings.DEFAULT_TIMEZONE
    rendered = render_jinja_template(
        booting_template_path,
        css_url=settings.LOCAL_TICKET_CSS_URL,
        logo_url=settings.LOCAL_LOGO_FIGURE_URL,
        date=datetime.now(pytz.timezone(tz)).strftime('%d/%m/%Y %H:%M'),
        serial_number=_photobooth.serial_number,
        place=_photobooth.place.name if _photobooth.place else None,
        event=_photobooth.event.name if _photobooth.event else None,
        is_online=is_online()
    )
    ticket_base64 = get_screenshot(rendered)
    ticket_io = base64.b64decode(ticket_base64)
    ticket_path, ticket_length = get_pure_black_and_white_ticket(ticket_io)
    pos_data = png2pos(ticket_path)
    printer.print_ticket(pos_data)


def trigger_async():
    thr = Thread(target=trigger, args=(), kwargs={})
    thr.start()
    return thr


def update():
    """
    This will update the data in case it has been changed in the API
    """
    logger.info("Updating data...")

    current = db.get_photobooth()

    next = figure.Photobooth.get(settings.RESIN_UUID)

    if current.id != next['id']:
        db.update_photobooth(id=next['id'], serial_number=next.get('serial_number'))

    # check if we need to update the place
    place = next.get('place')

    if place and not current.place:
        p = db.create_place(place)
        db.update_photobooth(place=p)

    elif not place and current.place:
        db.delete(current.place)
        db.update_photobooth(place=None)

    elif place and current.place and place.get('id') != current.place.id:
        db.delete(current.place)
        p = db.create_place(place)
        db.update_photobooth(place=p)

    elif place and current.place and place.get('modified') > current.place.modified:
        db.update_place(current.place.id, name=place.get('name'), tz=place.get('tz'), modified=place.get('modified'))

    # check if we need to update the event
    event = next.get('event')
    if event and not current.event:
        e = db.create_event(event)
        db.update_photobooth(event=e)

    elif not event and current.event:
        db.delete(current.event)
        db.update_photobooth(event=None)

    elif event and current.event and event.get('id') != current.event.id:
        db.delete(current.event)
        e = db.create_event(event)
        db.update_photobooth(event=e)

    elif event and current.event and event.get('modified') > current.event.modified:
        db.update_event(current.event.id, name=event.get('name'), modified=event.get('modified'))

    # check if we need to update the ticket template
    ticket_template = next.get('ticket_template')

    if ticket_template and not current.ticket_template:
        t = db.update_or_create_ticket_template(ticket_template)
        db.update_photobooth(ticket_template=t)

    elif not ticket_template and current.ticket_template:
        db.delete(current.ticket_template)
        db.update_photobooth(ticket_template=None)

    elif ticket_template and current.ticket_template and ticket_template.get('id') != current.ticket_template.id:
        db.delete(current.ticket_template)
        t = db.update_or_create_ticket_template(ticket_template)
        db.update_photobooth(ticket_template=t)

    elif ticket_template and current.ticket_template and ticket_template.get('modified') > current.ticket_template.modified:
        db.update_or_create_ticket_template(ticket_template)

    logger.info("Data updated !")


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
        picture_path = join(settings.PICTURE_ROOT,  portrait['filename'])
        write_file(portrait['picture'], picture_path)
        portrait['picture'] = picture_path

        ticket_path = join(settings.TICKET_ROOT, portrait['filename'])
        write_file(portrait['ticket'], ticket_path)
        portrait['ticket'] = ticket_path

        portrait.pop('filename')

        db.create_portrait(portrait)


def upload_portrait_async(portrait):
    thr = Thread(target=upload_portrait, args=(portrait,), kwargs={})
    thr.start()


def upload_portraits():

    number_of_portraits = db.get_number_of_portraits_to_be_uploaded()
    if number_of_portraits == 0:
        logger.info('No portrait to be uploaded by worker')
    else:
        logger.info('There are %s to be uploaded...' % number_of_portraits)

    while True:
        portrait = db.get_portrait_to_be_uploaded()
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
                db.update_portrait(portrait.id, uploaded=True)
                logger.info('Portrait %s uploaded !' % portrait.code)
            except figure.BadRequestError as e:
                # Duplicate code or files empty
                logger.exception(e)
                db.delete(portrait)
            except IOError as e:
                logger.exception(e)
                if e.errno == errno.ENOENT:
                    # snapshot or ticket file may be corrupted, proceed with remaining tickets
                    db.delete(portrait)
                else:
                    break
            except Exception as e:
                logger.exception(e)
                break
        else:
            break


def update_paper_level(pixels):
    paper_level = db.update_paper_level(pixels)
    logger.info('Paper level is now %s percent, updating API...' % paper_level)
    figure.Photobooth.edit(
        settings.RESIN_UUID, data={'paper_level': paper_level})
    logger.info('API updated with new paper level!')


def update_paper_level_async(pixels):
    thr = Thread(target=update_paper_level, args=(pixels,), kwargs={})
    thr.start()


def update_mac_addresses():
    mac_addresses = get_mac_addresses()
    figure.Photobooth.edit(
        settings.RESIN_UUID, data={'mac_addresses': mac_addresses})


def update_mac_addresses_async():
    thr = Thread(target=update_mac_addresses, args=(), kwargs={})
    thr.start()


def claim_new_codes():
    if db.should_claim_code():
        logger.info('We are running out of codes, fetching new ones from API...')
        new_codes = figure.CodeList.claim()['codes']
        db.bulk_insert_codes(new_codes)
        logger.info('New codes fetched and saved !')


def claim_new_codes_async():
    thr = Thread(target=claim_new_codes, args=(), kwargs={})
    thr.start()


def is_online():
    # check if the device is online
    ping_host = '8.8.8.8'
    server = PingServer(ping_host)
    b = server.is_active
    server.close()
    return b

