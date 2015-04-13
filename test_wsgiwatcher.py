import pytest


PIDAPP = """


"""


@pytest.yield_fixture
def pidapp_file(tmpdir):
    """Return path to a file containing a simple WSGI application.

    File has top-level function ``get_application()`` which takes no arguments
    and returns a WSGI app which responds to all requests with its own
    PID. Also has top-level function ``serve_forever(app)`` which accepts an
    app and serves that app forever (using wsgiref) on the port specified in
    the environment variable ``WSGIWATCHER_TEST_PORT``.

    If run as a script, this file passes the two above callables to wsgiwatcher
    and starts up an auto-reloading server.

    """
    filepath = tmpdir / 'pidapp.py'
