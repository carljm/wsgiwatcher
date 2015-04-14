import os
from wsgiref.simple_server import make_server

from wsgiwatcher import watcher


def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [str('response').encode('utf-8')]


def serve_forever():
    host = os.environ.get('WSGIWATCHER_TEST_HOST', '127.0.0.1')
    port = int(os.environ.get('WSGIWATCHER_TEST_PORT', '8080'))
    server = make_server(host, port, application)
    server.serve_forever()


watcher.run(serve_forever)
