# -*- coding: utf8 -*-


from flask import Flask, send_from_directory

from . import processus
from . import settings

app = Flask(__name__)

@app.route('/resources/<path:path>')
def send_static(path):
    return send_from_directory(settings.STATIC_ROOT, path)

@app.route('/trigger')
def trigger():
    try:
        processus.run()
        return 'Processus executed successfully'
    except Exception as e:
        return e.message, 500

@app.route('/media/<path:path>')
def send_media(path):
    return send_from_directory(settings.MEDIA_ROOT, path)

@app.route('/')
def hello():
    return 'Welcome to Figure Raspbian'

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=8080)

