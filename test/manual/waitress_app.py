from waitress import serve

from wsgiwatcher import watcher


def handler_app(environ, start_response):
    response_body = b'Works fine'
    status = '200 OK'

    response_headers = [
        ('Content-Type', 'text/plain'),
    ]

    start_response(status, response_headers)

    return [response_body]


def serve_forever():
    serve(handler_app)

watcher.run(serve_forever)
