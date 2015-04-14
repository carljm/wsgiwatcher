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
        self.event.set()


class Monitor(Observer):
    def __init__(self, done_event, parent_pid, extra_files=None):
        super(Monitor, self).__init__()
        self.paths = set(extra_files or [])
        self.handler = FlagOnAnyChangeHandler(done_event)
        self.done_event = done_event
        self.parent_pid = parent_pid
        self.daemon = True
        self.poll_thread = threading.Thread(target=self.poll)
        self.poll_thread.daemon = True

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
        interrupt_main()

    def update_paths(self):
        """Check sys.modules for paths to add to our path set."""
        for dirname in get_module_dirs():
            if dirname not in self.paths:
                self.paths.add(dirname)
                self.schedule(self.handler, dirname)


class Worker(Process):
    def __init__(self, script_file, done_event, parent_pid):
        super(Worker, self).__init__()
        self.script_file = script_file
        self.done_event = done_event
        self.parent_pid = parent_pid

    def run(self):
        monitor = Monitor(
            self.done_event,
            self.parent_pid,
            extra_files=[os.path.dirname(os.path.abspath(self.script_file))],
        )
        monitor.start()

        with open(self.script_file) as f:
            code = compile(f.read(), self.script_file, 'exec')
            exec(code, {}, {})


def run_server_until_file_changes(script_file):
    worker_done = Event()
    worker = Worker(script_file, worker_done, os.getpid())
    worker.start()
    print("WSGIWatcher: started server with PID %s" % worker.pid)
    worker_done.wait()
    print("WSGIWatcher: terminating server with PID %s" % worker.pid)
    worker.terminate()
    print("WSGIWatcher: waiting for server with PID %s to quit" % worker.pid)
    worker.join()
    print("WSGIWatcher: server with PID %s done" % worker.pid)


def run(script_file):
    while True:
        run_server_until_file_changes(script_file)
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
