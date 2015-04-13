import os
from wsgiref.simple_server import make_server

from wsgiwatcher import watcher


def application(environ, start_response):
    start_response('200 OK', [('content-type', 'text/plain')])
    return [bytes(os.getpid())]


def get_application():
    return application


def serve_forever(app):
    host = os.environ['WSGIWATCHER_TEST_HOST']
    port = int(os.environ['WSGIWATCHER_TEST_PORT'])
    server = make_server(host, port, app)
    server.serve_forever()


watcher.run(get_application, serve_forever)
