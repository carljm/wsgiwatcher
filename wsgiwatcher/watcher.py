from __future__ import print_function

import importlib
from multiprocessing import Process, Queue, Event
import os
try:
    import queue
except ImportError:
    import Queue as queue
try:
    from _thread import interrupt_main
except ImportError:
    from thread import interrupt_main
import threading
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CallbackHandler(FileSystemEventHandler):
    def __init__(self, paths, callback):
        super(CallbackHandler, self).__init__()
        self.paths = paths
        self.callback = callback

    def on_any_event(self, event):
        print("got event on path %s" % event.src_path)
        if event.src_path in self.paths:
            print("event path matched!")
            self.callback()


class Monitor(Observer):
    def __init__(self, callback):
        super(Monitor, self).__init__()
        self.paths = set()
        self.dirpaths = set()
        self.handler = CallbackHandler(self.paths, callback)

    def add_path(self, path):
        if path not in self.paths:
            self.paths.add(path)
            dirpath = os.path.dirname(path)
            if dirpath not in self.dirpaths:
                self.dirpaths.add(dirpath)
                self.schedule(self.handler, dirpath)


class PollSysModules(threading.Thread):
    def __init__(self, callback):
        super(PollSysModules, self).__init__()
        self.paths = set()
        self.callback = callback

    def run(self):
        while True:
            self.update_paths()
            time.sleep(1)

    def update_paths(self):
        """Check sys.modules for paths to add to our path set."""
        for path in get_module_paths():
            if path not in self.paths:
                self.paths.add(path)
                self.callback(path)


class WatchForParentShutdown(threading.Thread):
    def __init__(self, parent_pid):
        super(WatchForParentShutdown, self).__init__()
        self.parent_pid = parent_pid

    def run(self):
        # If parent shuts down (and we are adopted by a different parent
        # process), we should shut down.
        while (os.getppid() == self.parent_pid):
            time.sleep(0.5)

        interrupt_main()


class Worker(Process):
    def __init__(self, serve_forever_path, files_queue, parent_pid):
        super(Worker, self).__init__()
        self.serve_forever_path = serve_forever_path
        self.files_queue = files_queue
        self.parent_pid = parent_pid

    def run(self):
        modname, funcname = self.serve_forever_path.rsplit('.', 1)
        module = importlib.import_module(modname)
        func = getattr(module, funcname)

        poller = PollSysModules(self.files_queue.put)
        poller.start()

        parent_watcher = WatchForParentShutdown(self.parent_pid)
        parent_watcher.start()

        func()


def run_server_until_file_change(serve_forever_path, verbosity=0):
    files_queue = Queue()
    file_changed = Event()

    worker = Worker(serve_forever_path, files_queue, os.getpid())
    worker.daemon = True

    monitor = Monitor(lambda: file_changed.set())
    monitor.start()
    worker.start()

    print("started server with PID %s" % worker.pid)

    while (not file_changed.is_set()) and worker.is_alive():
        try:
            path = files_queue.get(timeout=1)
        except queue.Empty:
            pass
        else:
            if path.endswith('testapp.py'):
                print("adding %s to paths" % path)
            monitor.add_path(path)

    monitor.stop()
    print("Waiting for monitor thread in %s to quit" % worker.pid)
    monitor.join()
    print("Waiting for server %s to quit" % worker.pid)
    worker.terminate()
    worker.join()
    print("server with PID %s done" % worker.pid)


def run(serve_forever_path, verbosity=0):
    while True:
        run_server_until_file_change(serve_forever_path, verbosity)
        time.sleep(0.2)


def get_module_paths(modules=None):
    """Yield paths of all imported modules."""
    modules = modules or list(sys.modules.values())
    for module in modules:
        try:
            filename = module.__file__
        except (AttributeError, ImportError):
            continue
        if filename is not None:
            abs_filename = os.path.abspath(filename)
            if os.path.isfile(abs_filename):
                yield abs_filename
