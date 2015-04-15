from __future__ import print_function

from functools import partial
import importlib
from multiprocessing import Process, Event
import os
try:
    from _thread import interrupt_main
except ImportError:
    from thread import interrupt_main
import threading
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FlagOnAnyChangeHandler(FileSystemEventHandler):
    def __init__(self, event):
        super(FlagOnAnyChangeHandler, self).__init__()
        self.event = event

    def on_any_event(self, event):
        print('file event!')
        self.event.set()
        interrupt_main()


class Monitor(Observer):
    def __init__(self, done_event, parent_pid, extra_files=None):
        super(Monitor, self).__init__()
        self.paths = set(extra_files or [])
        self.handler = FlagOnAnyChangeHandler(done_event)
        self.done_event = done_event
        self.parent_pid = parent_pid
        self.poll_thread = threading.Thread(target=self.poll)

        for path in self.paths:
            self.schedule(self.handler, path)

    def run(self):
        self.update_paths()
        self.poll_thread.start()
        super(Observer, self).run()

    def poll(self):
        while (os.getppid() == self.parent_pid):
            time.sleep(1)
            self.update_paths()
        print('parent died, interrupting main thread')
        interrupt_main()

    def update_paths(self):
        """Check sys.modules for paths to add to our path set."""
        for dirname in get_module_dirs():
            if dirname not in self.paths:
                self.paths.add(dirname)
                self.schedule(self.handler, dirname)


class Worker(Process):
    def __init__(self, serve_forever_path, done_event, parent_pid):
        super(Worker, self).__init__()
        self.serve_forever_path = serve_forever_path
        self.done_event = done_event
        self.parent_pid = parent_pid

    def run(self):
        modname, funcname = self.serve_forever_path.rsplit('.', 1)
        module = importlib.import_module(modname)
        func = getattr(module, funcname)

        monitor = Monitor(self.done_event, self.parent_pid)
        monitor.start()

        func()


def run_server_until_file_changes(serve_forever_path, verbosity=0):
    worker_done = Event()
    worker = Worker(serve_forever_path, worker_done, os.getpid())
    worker.start()
    log = Log(verbosity)
    log.info("started server with PID %s" % worker.pid)
    log.debug("waiting for server with PID %s to quit" % worker.pid)
    worker.join()
    log.info("server with PID %s done" % worker.pid)


class Log(object):
    def __init__(self, verbosity):
        self.debug = self.info = lambda s: None
        if verbosity:
            self.info = partial(self.send, level='info')
            if verbosity > 1:
                self.debug = partial(self.send, level='debug')

    def send(self, s, level):
        print("WSGIWatcher (%s): %s" % (level, s))


def run(serve_forever_path, verbosity=0):
    while True:
        run_server_until_file_changes(serve_forever_path, verbosity)
        time.sleep(0.5)


def get_module_dirs(modules=None):
    """Yield directories containing imported modules."""
    modules = modules or list(sys.modules.values())
    for module in modules:
        try:
            filename = module.__file__
        except (AttributeError, ImportError):
            continue
        if filename is not None:
            dirname = os.path.dirname(os.path.abspath(filename))
            if os.path.isdir(dirname):
                yield dirname
