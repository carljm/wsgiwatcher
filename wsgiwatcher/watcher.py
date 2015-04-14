from multiprocessing import Process
import os
import threading
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FlagOnAnyChangeHandler(FileSystemEventHandler):
    def __init__(self):
        super(FlagOnAnyChangeHandler, self).__init__()
        self.file_changed = False

    def on_any_event(self, event):
        self.file_changed = True


class Monitor(Observer):
    def __init__(self):
        super(Monitor, self).__init__()
        self.module_ids = set()
        self.paths = set()
        self.handler = FlagOnAnyChangeHandler()
        self.daemon = True

    def changed(self):
        return self.handler.file_changed

    def run(self):
        self.update_paths()
        super(Observer, self).run()

    def update_paths(self):
        """Check sys.modules for paths to add to our path set."""
        modules = list(sys.modules.values())
        for module in modules:
            module_id = id(module)
            if module_id in self.module_ids:
                continue
            self.module_ids.add(module_id)
            try:
                filename = module.__file__
            except (AttributeError, ImportError):
                continue
            if filename is not None:
                dirname = os.path.dirname(filename)
                if os.path.isdir(dirname) and dirname not in self.paths:
                    self.paths.add(dirname)
                    self.schedule(self.handler, dirname)


class Server(threading.Thread):
    def __init__(self, get_application, serve_forever):
        super(Server, self).__init__()
        self.get_application = get_application
        self.serve_forever = serve_forever
        self.daemon = True

    def run(self):
        app = self.get_application()
        self.serve_forever(app)


class Worker(Process):
    def __init__(self, get_application, serve_forever, parent_pid):
        super(Worker, self).__init__()
        self.get_application = get_application
        self.serve_forever = serve_forever
        self.parent_pid = parent_pid

    def run(self):
        server = Server(self.get_application, self.serve_forever)
        server.start()

        monitor = Monitor()
        monitor.start()

        # Continue until a file changes or our parent goes away.
        while (os.getppid() == self.parent_pid) and not monitor.changed():
            time.sleep(1)
            monitor.update_paths()


def run_server_until_file_changes(get_application, serve_forever):
    worker = Worker(get_application, serve_forever, os.getpid())
    worker.start()
    print("WSGIWatcher: started server with PID %s" % worker.pid)
    worker.join()
    print("WSGIWatcher: server with PID %s done" % worker.pid)


def run(get_application, serve_forever):
    while True:
        run_server_until_file_changes(get_application, serve_forever)
        time.sleep(0.5)
