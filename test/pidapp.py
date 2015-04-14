import os
from wsgiref.simple_server import make_server

from wsgiwatcher import watcher


def application(environ, start_response):
    start_response('200 OK', [('content-type', 'text/plain')])
    return [bytes(os.getpid())]


def serve_forever():
    host = os.environ['WSGIWATCHER_TEST_HOST']
    port = int(os.environ['WSGIWATCHER_TEST_PORT'])
    server = make_server(host, port, application)
    server.serve_forever()


watcher.run(serve_forever)
