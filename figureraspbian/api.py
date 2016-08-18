# -*- coding: utf8 -*-
from os.path import basename, dirname

from flask import Flask, send_from_directory, request, flash, redirect
from werkzeug.utils import secure_filename
import psutil
from PIL import Image

from figureraspbian import photobooth
from figureraspbian import db, settings
from figureraspbian.exceptions import DevicesBusy

app = Flask(__name__)


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


@app.route('/test_template', methods=['GET', 'POST'])
def test_template():
    """ Print a ticket with the picture uploaded by the user """
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            picture = Image.open(file)
            w, h = picture.size
            if w != h:
                flash('The picture must have a square shape')
                return redirect(request.url)
            exif_bytes = picture.info['exif']
            photobooth.render_print_and_upload(picture, exif_bytes)
            return u'Ticket successfully printed'

    return u'''
    <!doctype html>
    <title>Upload a Picture</title>
    <h1>Upload a picture to print a ticket</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@app.route('/door_open')
def door_open():
    photobooth.door_open()
    return u'Door opened'


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


@app.route('/acquire_lock')
def acquire_lock():
    acquired = photobooth.lock.acquire(False)
    if acquired:
        return 'Lock acquired'
    else:
        return 'Could not acquire the lock'


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







