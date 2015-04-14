from __future__ import unicode_literals


def test_testapp_responds_with_200_status(testapp):
    testapp.get('/', status=200)


def test_testapp_reloads_after_file_changed(
        testapp, copy_testapp_file_with_response, wait_for_response):
    body1 = testapp.get('/', status=200).body

    assert body1 == b'response'

    copy_testapp_file_with_response('new response')
    resp = wait_for_response(lambda r: r.body == b'new response')

    assert resp.body == b'new response'


def test_kills_worker_processes(testapp_process, wait_for_response):
    """Shutting down monitor master process kills worker processes."""
    testapp_process.terminate()
    # Terminate() just sends SIGTERM, now we wait for it to actually terminate
    testapp_process.wait()

    resp = wait_for_response(lambda r: r.status_code == 502)

    assert resp.status_code == 502


def test_syntax_error_doesnt_kill_watcher(
        testapp, append_to_testapp_file, wait_for_response):
    """Adding a syntax error to app kills server, but not watcher."""
    append_to_testapp_file('\nif True:\n')  # this is a syntax error

    wait_for_response(lambda r: r.status_code == 502)

    append_to_testapp_file('    pass\n')  # now it's not!

    wait_for_response(lambda r: r.status_code == 200)
