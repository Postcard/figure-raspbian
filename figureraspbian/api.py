# -*- coding: utf8 -*-
from flask import Flask, request
from figureraspbian import photobooth

app = Flask(__name__)


@app.route('/trigger')
def trigger():
    return photobooth.trigger()


def start_server():
    app.run(host='0.0.0.0', port=80)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()



