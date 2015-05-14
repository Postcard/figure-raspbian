# -*- coding: utf8 -*-


from flask import Flask, send_from_directory

from . import settings

app = Flask(__name__)


@app.route('/resources/<path:path>')
def send_static(path):
    return send_from_directory(settings.STATIC_ROOT, path)

@app.route('/media/<path:path>')
def send_media(path):
    return send_from_directory(settings.MEDIA_ROOT, path)
