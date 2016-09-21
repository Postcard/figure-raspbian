# -*- coding: utf8 -*-
from os.path import basename, dirname, join

from flask import Flask, send_from_directory, request, flash, redirect, abort
import psutil
from PIL import Image

from figureraspbian import photobooth
from figureraspbian import db, settings, utils
from figureraspbian.exceptions import DevicesBusy, OutOfPaperError

app = Flask(__name__)


def login_required(func):
    """ A decorator that ensures the request is made by an admin user """
    def wrapper(*args, **kwargs):
        token = request.args.get('token', '')
        if token != settings.TOKEN:
            abort(401)
        return func(*args, **kwargs)
    return wrapper


@login_required
@app.route('/trigger')
def trigger():
    try:
        ticket_path = photobooth._trigger()
        return send_from_directory(dirname(ticket_path), basename(ticket_path))
    except DevicesBusy:
        message = u'Someone else just triggered the photobooth, try again later'
        return message


ALLOWED_EXTENSIONS = ['jpg', 'JPEG', 'JPG']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@login_required
@app.route('/test_template', methods=['GET', 'POST'])
def test_template():
    """ Print a ticket with the picture uploaded by the user """
    if request.method == 'POST':
        # check if the post request has the file part
        if 'picture' not in request.files:
            flash('No file part')
            return redirect(request.url)
        picture_file = request.files['picture']
        # if user does not select file, browser also
        # submit a empty part without filename
        if picture_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if picture_file and allowed_file(picture_file.filename):
            picture = Image.open(picture_file)
            w, h = picture.size
            if w != h:
                flash('The picture must have a square shape')
                return redirect(request.url)
            exif_bytes = picture.info['exif'] if 'exif' in picture.info else None
            photobooth.render_print_and_upload(picture, exif_bytes)
            return u'Ticket successfully printed'

    return u'''
    <!doctype html>
    <title>Upload a Picture</title>
    <h1>Upload a picture to print a ticket</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=picture>
         <input type=submit value=Upload>
    </form>
    '''


@login_required
@app.route('/print', methods=['GET', 'POST'])
def print_image():
    """ Print the image uploaded by the user """
    if request.method == 'POST':
        # check if the post request has the file part
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        image_file = request.files['image']
        # if user does not select file, browser also
        # submit a empty part without filename
        if image_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if image_file and allowed_file(image_file.filename):
            im = Image.open(image_file)
            w, h = im.size
            if w != settings.PRINTER_MAX_WIDTH:
                ratio = settings.PRINTER_MAX_WIDTH / w
                im = im.resize((settings.PRINTER_MAX_WIDTH, h * ratio))
            if im.mode != '1':
                im = im.convert('1')

            im_path = join(settings.MEDIA_ROOT, 'test.png')
            im.save(im_path, im.format, quality=100)
            pos_data = utils.png2pos(im_path)

            try:
                photobooth.printer.print_ticket(pos_data)
            except OutOfPaperError:
                return u'Out of paper'
            return u'Ticket successfully printed'

    return u'''
    <!doctype html>
    <title>Upload an image</title>
    <h1>Upload an image to print it in the photobooth</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=image>
         <input type=submit value=Upload>
    </form>
    '''


@login_required
@app.route('/door_open')
def door_open():
    photobooth.door_open()
    return u'Door opened'


@login_required
@app.route('/logs')
def logs():
    resp = send_from_directory('/data/log', 'figure.log')
    resp.headers['Content-Disposition'] = 'attachment; filename="figure.log"'
    return resp


@login_required
@app.route('/info')
def info():
    photobooth = db.get_photobooth()
    place = photobooth.place.name if photobooth.place else ''
    identifier = photobooth.serial_number or settings.RESIN_UUID
    number_of_portraits_to_be_uploaded = db.get_portrait_to_be_uploaded() or 0
    html = u"""
    <h1>Figure photobooth {identifier}</h1>
    </br>
    <p>Place: {place}</p>
    <p>Photo counter: {counter}</p>
    <p>Number of portraits to be uploaded: {number_of_portraits_to_be_uploaded}<p>
    """.format(
        identifier=identifier,
        place=place,
        counter=photobooth.counter,
        number_of_portraits_to_be_uploaded=number_of_portraits_to_be_uploaded
    )
    return html


@login_required
@app.route('/system')
def system():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_usage_percent = psutil.disk_usage('/').percent
    number_of_processes = len(psutil.pids())
    html = u"""
    <p>cpu: {cpu_percent}%</p>
    <p>memory: {memory_percent}%</p>
    <p>disk_usage: {disk_usage_percent}%</p>
    <p>number of processes: {number_of_processes}</p>
    """.format(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_usage_percent=disk_usage_percent,
        number_of_processes=number_of_processes
    )
    return html


@login_required
@app.route('/acquire_lock')
def acquire_lock():
    acquired = photobooth.lock.acquire(False)
    if acquired:
        return 'Lock acquired'
    else:
        return 'Could not acquire the lock'


@login_required
@app.route('/release_lock')
def release_lock():
    try:
        photobooth.lock.release()
    except Exception:
        pass
    finally:
        return 'Lock released'


def start_server():
    app.run(host='0.0.0.0', port=80)







