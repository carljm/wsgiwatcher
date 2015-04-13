from multiprocessing import Process, Event
import os
import threading
import time
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Monitor(FileSystemEventHandler):
    def __init__(self, done, poll_interval=1):
        self.done = done
        self.poll_interval = poll_interval
        self.paths = set()
        self.observer_thread = None
        self.poll_thread = None

    def watch_for_changes(self):
        self.observer_thread = Observer()
        self.observer_thread.setDaemon(True)

        self.update_paths()

        self.observer_thread.start()

        while not self.done.is_set():
            time.sleep(self.poll_interval)
            self.update_paths()

    def on_any_event(self, event):
        self.done.set()

    def update_paths(self):
        """Check sys.modules for paths to add to our path set."""
        for module in sys.modules.values():
            try:
                filename = module.__file__
            except (AttributeError, ImportError):
                continue
            if filename is not None:
                dirname = os.path.dirname(filename)
                if dirname not in self.paths:
                    self.paths.add(dirname)
                    self.observer_thread.schedule(self, dirname)


def start_worker(get_application, serve_forever, worker_done):
    app = get_application()

    server_thread = threading.Thread(target=serve_forever, args=[app])
    server_thread.setDaemon(True)
    server_thread.start()

    monitor = Monitor(worker_done)
    monitor.watch_for_changes()


def start_worker_process(get_application, serve_forever):
    worker_done = Event()
    worker = Process(
        target=start_worker,
        args=(get_application, serve_forever, worker_done),
    )
    worker.start()
    while not worker_done.is_set():
        time.sleep(0.2)


def run(get_application, serve_forever):
    while True:
        start_worker_process(get_application, serve_forever)
        time.sleep(0.5)
