# -*- coding: utf8 -*-
from functools import wraps
import cStringIO

from flask import Flask, send_from_directory, request, jsonify, send_file
import psutil
from PIL import Image


from threads import rlock
from photobooth import get_photobooth
from models import Photobooth, Portrait
import settings
from exceptions import DevicesBusy, PhotoboothNotReady, OutOfPaperError

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


@app.route('/focus', methods=['POST'])
@login_required
def focus():
    try:
        steps = request.values.get('focus_steps')
        photobooth = get_photobooth()
        if steps:
            photobooth.focus_camera(int(steps))
        else:
            photobooth.focus_camera()
        return jsonify(message='Camera focused')
    except DevicesBusy:
        return jsonify(error='the photobooth is busy'), 423


@app.route('/trigger', methods=['POST'])
@login_required
def trigger():
    try:
        photobooth = get_photobooth()
        ticket = photobooth.trigger()
        return send_file(cStringIO.StringIO(ticket), mimetype='jpg')
    except DevicesBusy:
        return jsonify(error='the photobooth is busy'), 423
    except PhotoboothNotReady:
        return jsonify(erro='the photobooth is not ready or not initialized properly'), 423


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
        photobooth = get_photobooth()
        photobooth.render_print_and_upload(picture_file.getvalue())
        return jsonify(message='Ticket successfully printed')


@app.route('/print', methods=['POST'])
@login_required
def print_image():
    """ Print the image uploaded by the user """
    image_file = request.files['image']
    if image_file and allowed_file(image_file.filename):
        try:
            photobooth = get_photobooth()
            photobooth.print_image(image_file.getvalue())
        except DevicesBusy:
            return jsonify(error='the photobooth is busy'), 423
        except OutOfPaperError:
            return jsonify(error='Out of paper'), 500
        return jsonify(message='Ticket printed succesfully')


@app.route('/door_open', methods=['POST'])
@login_required
def door_open():
    photobooth = get_photobooth()
    photobooth.unlock_door()
    return jsonify(message='Door opened')


@app.route('/info')
@login_required
def info():
    photobooth = Photobooth.get()
    place = photobooth.place.name if photobooth.place else ''
    identifier = photobooth.serial_number or settings.RESIN_UUID
    portraits_not_uploaded_count = Portrait.not_uploaded_count()
    res = {
        'identifier': identifier,
        'place': place,
        'counter': photobooth.counter,
        'number_of_portraits_to_be_uploaded': portraits_not_uploaded_count
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
    acquired = rlock.acquire(False)
    if acquired:
        return jsonify(message='Lock acquired')
    else:
        return jsonify(message='Could not acquire the lock')


@app.route('/release_lock', methods=['POST'])
@login_required
def release_lock():
    try:
        rlock.release()
    except Exception:
        pass
    finally:
        return jsonify(message='Lock released')


def start_server():
    app.run(host='0.0.0.0', port=80)







