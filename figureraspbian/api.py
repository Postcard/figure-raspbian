# -*- coding: utf8 -*-
from os.path import basename, dirname, join
from functools import wraps

from flask import Flask, send_from_directory, request, abort, jsonify
import psutil
from PIL import Image

from figureraspbian import photobooth
from figureraspbian import db, settings, utils
from figureraspbian.exceptions import DevicesBusy, OutOfPaperError

app = Flask(__name__)


def login_required(func):
    """ A decorator that ensures the request is made by an admin user """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if token != settings.TOKEN:
            return jsonify(error='Not authorized'), 401
        return func(*args, **kwargs)
    return decorated_function


@app.route('/trigger', methods=['POST'])
@login_required
def trigger():
    try:
        ticket_path = photobooth._trigger()
        return send_from_directory(dirname(ticket_path), basename(ticket_path))
    except DevicesBusy:
        return jsonify(error='the photobooth is busy'), 423


ALLOWED_EXTENSIONS = ['jpg', 'JPEG', 'JPG', 'png', 'PNG', 'gif']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/test_template', methods=['POST'])
@login_required
def test_template():
    """ Print a ticket with the picture uploaded by the user """
    picture_file = request.files['picture']
    if picture_file and allowed_file(picture_file.filename):
        picture = Image.open(picture_file)
        w, h = picture.size
        if w != h:
            return jsonify(error='The picture must have a square shape'), 400
        exif_bytes = picture.info['exif'] if 'exif' in picture.info else None
        photobooth.render_print_and_upload(picture, exif_bytes)
        return jsonify(message='Ticket successfully printed')


@app.route('/print', methods=['POST'])
@login_required
def print_image():
    """ Print the image uploaded by the user """

    image_file = request.files['image']
    if image_file and allowed_file(image_file.filename):
        im = Image.open(image_file)
        w, h = im.size
        if w != settings.PRINTER_MAX_WIDTH:
            ratio = float(settings.PRINTER_MAX_WIDTH) / w
            im = im.resize((settings.PRINTER_MAX_WIDTH, int(h * ratio)))
        if im.mode != '1':
            im = im.convert('1')
        im_path = join(settings.MEDIA_ROOT, 'test.png')
        im.save(im_path, im.format, quality=100)
        pos_data = utils.png2pos(im_path)

        try:
            photobooth.printer.print_ticket(pos_data)
        except OutOfPaperError:
            return jsonify(error='Out of paper'), 500
        return jsonify(message='Ticket printed succesfully')


@app.route('/door_open', methods=['POST'])
@login_required
def door_open():
    photobooth.door_open()
    return jsonify(message='Door opened')


@app.route('/logs')
@login_required
def logs():
    resp = send_from_directory('/data/log', 'figure.log')
    resp.headers['Content-Disposition'] = 'attachment; filename="figure.log"'
    return resp


@app.route('/info')
@login_required
def info():
    photobooth = db.get_photobooth()
    place = photobooth.place.name if photobooth.place else ''
    identifier = photobooth.serial_number or settings.RESIN_UUID
    number_of_portraits_to_be_uploaded = db.get_portrait_to_be_uploaded() or 0
    res = {
        'identifier': identifier,
        'place': place,
        'counter': photobooth.counter,
        'number_of_portraits_to_be_uploaded': number_of_portraits_to_be_uploaded
    }
    return jsonify(**res)


@app.route('/system')
@login_required
def system():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_usage_percent = psutil.disk_usage('/').percent
    number_of_processes = len(psutil.pids())
    res = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_usage_percent': disk_usage_percent,
        'number_of_processes': number_of_processes
    }
    return jsonify(**res)


@app.route('/acquire_lock', methods=['POST'])
@login_required
def acquire_lock():
    acquired = photobooth.lock.acquire(False)
    if acquired:
        return jsonify(message='Lock acquired')
    else:
        return jsonify(message='Could not acquire the lock')


@app.route('/release_lock', methods=['POST'])
@login_required
def release_lock():
    try:
        photobooth.lock.release()
    except Exception:
        pass
    finally:
        return jsonify(message='Lock released')


def start_server():
    app.run(host='0.0.0.0', port=80)







