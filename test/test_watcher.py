def test_pidapp_responds_with_200_status(pidapp):
    pidapp.get('/', status=200)


def test_pidapp_reloads_after_file_changed(pidapp_file, pidapp, wait_for_response):
    pid1 = pidapp.get('/', status=200).body
    import os
    os.utime(pidapp_file, None)  # "touch"
    resp = wait_for_response(lambda r: r.body != pid1)
    assert resp.body != pid1
