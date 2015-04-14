def serve_forever():
    import os
    from wsgiref.simple_server import make_server

    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [str('response').encode('utf-8')]

    host = os.environ.get('WSGIWATCHER_TEST_HOST', '127.0.0.1')
    port = int(os.environ.get('WSGIWATCHER_TEST_PORT', '8080'))
    server = make_server(host, port, application)
    server.serve_forever()


serve_forever()
