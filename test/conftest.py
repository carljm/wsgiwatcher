import os
from subprocess import Popen
import sys
import time

import py.path
import pytest
from webtest import TestApp
from webtest.http import get_free_port


HERE = py.path.local(__file__).dirpath()

TESTAPP_HOST_ENVVAR = 'WSGIWATCHER_TEST_HOST'
TESTAPP_PORT_ENVVAR = 'WSGIWATCHER_TEST_PORT'


@pytest.fixture
def testapp_file_source_path():
    return HERE / 'testapp.py'


@pytest.fixture
def testapp_file_target_path(tmpdir):
    return tmpdir / 'testapp.py'


@pytest.fixture
def testapp_file_contents(testapp_file_source_path):
    return testapp_file_source_path.read()


@pytest.fixture
def testapp_file(tmpdir, testapp_file_source_path, testapp_file_target_path):
    """Return path to a file containing a simple WSGI application.

    File has top-level function ``serve_forever()`` which serves the app
    forever (using wsgiref) on the host and port specified in the environment
    variables ``WSGIWATCHER_TEST_HOST`` and ``WSGIWATCHER_TEST_PORT``.

    """
    testapp_file_source_path.copy(testapp_file_target_path)
    return str(testapp_file_target_path)


@pytest.yield_fixture
def _testapp_process_host_port(tmpdir, testapp_file):
    """Execute watcher in subprocess; yield (popen-obj, host, port)."""
    host, port = get_free_port()
    os.chdir(str(tmpdir))
    process = Popen(
        [
            sys.executable,
            '-c',
            (
                "from wsgiwatcher import watcher; "
                "watcher.run('testapp.serve_forever', 1)"
            ),
        ],
        env={
            TESTAPP_HOST_ENVVAR: host,
            TESTAPP_PORT_ENVVAR: str(port),
            'PYTHONDONTWRITEBYTECODE': '1',
        },
    )
    yield (process, host, port)
    # Only shut down if we haven't been shut down already.
    if process.poll() is None:
        process.terminate()
        process.wait()


@pytest.fixture
def testapp_process(_testapp_process_host_port):
    """Return the Popen object for the running testapp server."""
    return _testapp_process_host_port[0]


@pytest.fixture
def testapp_url(_testapp_process_host_port):
    """Return the URL for the running testapp server."""
    _, host, port = _testapp_process_host_port
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
def testapp(testapp_url):
    """Return WebTest TestApp wrapper around ``testapp_url``."""
    app = TestApp(testapp_url)

    # Wait until we're actually serving requests
    def check_response():
        resp = app.get('/', expect_errors=True)
        if resp.status_code == 200:
            return resp
        return False
    _wait_for(check_response)
    return app


@pytest.fixture
def wait_for_response(testapp):
    def _wait_for_response(
            success_condition, retries=10, interval=1, initial_wait=1):
        def check_response():
            resp = testapp.get('/', expect_errors=True)
            if success_condition(resp):
                return resp
            return False
        time.sleep(initial_wait)
        return _wait_for(check_response, retries=retries, interval=interval)
    return _wait_for_response


@pytest.fixture
def append_to_testapp_file(testapp_file):
    def _append(text):
        with open(testapp_file, 'a') as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    return _append


@pytest.fixture
def copy_testapp_file_with_response(
        testapp_file_contents, testapp_file_target_path):
    def _replace_and_copy(response_text):
        new_contents = testapp_file_contents.replace(
            "'response'", "'%s'" % response_text)
        with testapp_file_target_path.open('w') as fh:
            fh.write(new_contents)
            fh.flush()
            os.fsync(fh.fileno())
    return _replace_and_copy
