# -*- coding: utf8 -*-

from flask import Flask, request
server = Flask(__name__, host='0.0.0.0', port=80)

from figureraspbian import photobooth


@server.route('/trigger')
def trigger():
    return photobooth.trigger()


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()



