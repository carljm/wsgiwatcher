from __future__ import unicode_literals


def test_pidapp_responds_with_200_status(pidapp):
    pidapp.get('/', status=200)


def test_pidapp_reloads_after_file_changed(
        pidapp, append_to_pidapp_file, wait_for_response):
    pid1 = pidapp.get('/', status=200).body
    append_to_pidapp_file('\n')
    resp = wait_for_response(lambda r: r.body != pid1)
    assert resp.body != pid1


def test_kills_worker_processes(pidapp_process, wait_for_response):
    """Shutting down monitor master process kills worker processes."""
    pidapp_process.terminate()
    # Terminate() just sends SIGTERM, now we wait for it to actually terminate
    pidapp_process.wait()

    resp = wait_for_response(lambda r: r.status_code == 502)

    assert resp.status_code == 502


def test_syntax_error_doesnt_kill_watcher(
        pidapp, append_to_pidapp_file, wait_for_response):
    """Adding a syntax error to app kills server, but not watcher."""
    append_to_pidapp_file('\nif True:\n')  # this is a syntax error

    wait_for_response(lambda r: r.status_code == 502)

    append_to_pidapp_file('    pass\n')  # now it's not!

    wait_for_response(lambda r: r.status_code == 200)
