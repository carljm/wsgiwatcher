WSGI Watcher
============

WSGI Watcher is a tool to aid in the development of apps using the
Web Server Gateway Interface (WSGI) by watching for changed source files
and reloading the server.

WSGI Watcher aims for compatibility with multiple WSGI server implementations
on multiple platforms. It has been tested on CPython 2.6-3.4, PyPy, and PyPy3
on Linux and OS X.

It uses the `watchdog <https://pypi.python.org/pypi/watchdog>`_ library for
cross-platform support for notification of file changes.


Extended Documentation
----------------------

.. toctree::
   :maxdepth: 1

   api.rst
