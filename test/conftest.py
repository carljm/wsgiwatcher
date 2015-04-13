from subprocess import Popen
import sys
import time

import py.path
import pytest
from webtest import TestApp
from webtest.http import get_free_port


HERE = py.path.local(__file__).dirpath()

PIDAPP_HOST_ENVVAR = 'WSGIWATCHER_TEST_HOST'
PIDAPP_PORT_ENVVAR = 'WSGIWATCHER_TEST_PORT'


@pytest.fixture
def pidapp_file(tmpdir):
    """Return path to a file containing a simple WSGI application.

    File has top-level function ``get_application()`` which takes no arguments
    and returns a WSGI app which responds to all requests with its own
    PID. Also has top-level function ``serve_forever(app)`` which accepts an
    app and serves that app forever (using wsgiref) on the host and port
    specified in the environment variables ``WSGIWATCHER_TEST_HOST`` and
    ``WSGIWATCHER_TEST_PORT``.

    If run as a script, this file passes the two above callables to wsgiwatcher
    and starts up an auto-reloading server.

    """
    source = HERE / 'pidapp.py'
    target = tmpdir / 'pidapp.py'
    source.copy(target)
    return str(target)


@pytest.yield_fixture
def _pidapp_process_host_port(pidapp_file):
    """Execute ``pidapp_file`` in subprocess; yield (popen-obj, host, port)."""
    host, port = get_free_port()
    process = Popen(
        [sys.executable, str(pidapp_file)],
        env={PIDAPP_HOST_ENVVAR: host, PIDAPP_PORT_ENVVAR: str(port)},
    )
    yield (process, host, port)
    process.terminate()


@pytest.fixture
def pidapp_process(_pidapp_process_host_port):
    """Return the Popen object for the running pidapp server."""
    return _pidapp_process_host_port[0]


@pytest.fixture
def pidapp_url(_pidapp_process_host_port):
    """Return the URL for the running pidapp server."""
    _, host, port = _pidapp_process_host_port
    return 'http://%s:%s' % (host, port)


class TimeoutException(Exception):
    pass


def _wait_for(checker, retries=5, interval=0.1):
    for i in range(retries):
        time.sleep(interval)
        result = checker()
        if result:
            return result
    raise TimeoutException('Timed out after {} retries'.format(retries))


@pytest.fixture
def pidapp(pidapp_url):
    """Return WebTest TestApp wrapper around ``pidapp_url``."""
    app = TestApp(pidapp_url)

    # Wait until we're actually serving requests
    def check_response():
        resp = app.get('/', expect_errors=True)
        if resp.status_code == 200:
            return resp
        return False
    _wait_for(check_response)
    return app


@pytest.fixture
def wait_for_response(pidapp):
    def _wait_for_response(success_condition, retries=5):
        def check_response():
            resp = pidapp.get('/', expect_errors=True)
            if success_condition(resp):
                return resp
            return False
        return _wait_for(check_response, retries=retries)
    return _wait_for_response
