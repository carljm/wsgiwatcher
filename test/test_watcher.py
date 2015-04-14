import os

from pretend import stub

from wsgiwatcher import watcher


HERE = os.path.dirname(__file__)


class TestGetModuleDirs(object):
    def test_yields_dirnames_of_module_files(self):
        modules = [stub(**{'__file__': __file__})]
        paths = list(watcher.get_module_dirs(modules))

        assert paths == [os.path.dirname(__file__)]

    def test_bypasses_if_no_file(self):
        modules = [stub(), stub(**{'__file__': None})]
        paths = list(watcher.get_module_dirs(modules))

        assert paths == []

    def test_bypasses_if_dir_does_not_exist(self):
        modules = [stub(**{'__file__': '/does/not/exist'})]
        paths = list(watcher.get_module_dirs(modules))

        assert paths == []

    def test_makes_path_absolute(self):
        modules = [stub(**{'__file__': 'foo.py'})]
        old_dir = os.getcwd()
        os.chdir(HERE)
        try:
            paths = list(watcher.get_module_dirs(modules))
        finally:
            os.chdir(old_dir)

        assert paths == [os.path.dirname(__file__)]
