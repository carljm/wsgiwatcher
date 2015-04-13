def test_pidapp_responds_with_200_status(pidapp):
    pidapp.get('/', status=200)
