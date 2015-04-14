from multiprocessing import Process, Event
import os
import threading
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Monitor(FileSystemEventHandler):
    def __init__(self, files_changed_event, parent_pid, poll_interval=1):
        self.files_changed_event = files_changed_event
        self.parent_pid = parent_pid
        self.poll_interval = poll_interval
        self.paths = set()
        self.observer_thread = None
        self.poll_thread = None

    def watch_until_changes(self):
        self.observer_thread = Observer()
        self.observer_thread.setDaemon(True)

        self.update_paths()

        self.observer_thread.start()

        while not self.files_changed_event.is_set():
            time.sleep(self.poll_interval)
            if os.getppid() != self.parent_pid:
                # Our parent has gone away, we should too
                break
            self.update_paths()

    def on_any_event(self, event):
        self.files_changed_event.set()

    def update_paths(self):
        """Check sys.modules for paths to add to our path set."""
        modules = list(sys.modules.values())
        for module in modules:
            try:
                filename = module.__file__
            except (AttributeError, ImportError):
                continue
            if filename is not None:
                dirname = os.path.dirname(filename)
                if os.path.isdir(dirname) and dirname not in self.paths:
                    self.paths.add(dirname)
                    self.observer_thread.schedule(self, dirname)


class Worker(Process):
    def __init__(self, get_application, serve_forever, done, parent_pid):
        super(Worker, self).__init__()
        self.get_application = get_application
        self.serve_forever = serve_forever
        self.done = done
        self.parent_pid = parent_pid

    def run(self):
        app = self.get_application()

        server_thread = threading.Thread(target=self.serve_forever, args=[app])
        server_thread.setDaemon(True)
        server_thread.start()

        monitor = Monitor(self.done, self.parent_pid)
        monitor.watch_until_changes()


def run_server_until_file_changes(get_application, serve_forever):
    worker_done = Event()
    worker = Worker(get_application, serve_forever, worker_done, os.getpid())
    worker.start()
    while not worker_done.is_set():
        time.sleep(0.2)


def run(get_application, serve_forever):
    while True:
        run_server_until_file_changes(get_application, serve_forever)
        time.sleep(0.5)
