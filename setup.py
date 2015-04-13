import os
from setuptools import setup, find_packages

install_requires = [
    'watchdog',
]

docs_extras = [
    'Sphinx',
    'docutils',
]

testing_extras = [
    'pytest',
    'pytest-cov',
    'WebTest',
    'WSGIProxy2',
]

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

setup(
    name='wsgiwatcher',
    version='1.0.dev0',
    author='Carl Meyer, David Glick',
    author_email='',
    description='Reload a WSGI server when files change',
    long_description=README + '\n\n' + CHANGES,
    license='MIT',
    keywords='wsgi server reload watch',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
    ],
    url='https://github.com/carljm/wsgiwatcher',
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
        'docs': docs_extras,
    },
    include_package_data=True,
    zip_safe=False,
)
