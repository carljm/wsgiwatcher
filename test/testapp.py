import os
from wsgiref.simple_server import make_server


def application(environ, start_response):
    headers = [
        ('Content-Type', 'text/plain'),
        ('X-Server-PID', str(os.getpid())),
        ('X-Server-Path', __file__),
    ]
    start_response('200 OK', headers)
    return [str('response').encode('utf-8')]


def serve_forever():
    host = os.environ.get('WSGIWATCHER_TEST_HOST', '127.0.0.1')
    port = int(os.environ.get('WSGIWATCHER_TEST_PORT', '8080'))
    server = make_server(host, port, application)
    server.serve_forever()
