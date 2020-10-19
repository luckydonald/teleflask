# -*- coding: utf-8 -*-
from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from os import path
__author__ = 'luckydonald'

here = path.abspath(path.dirname(__file__))

long_description = """A Python module that connects to the Telegram bot api, allowing to interact with Telegram users or groups."""


SYNC_REQUIREMENTS = [
    'pytgbot[sync]',
    'requests', "requests[security]",  # connect with the internet in general
]
ASYNC_REQUIREMENTS = [
    'pytgbot[async]',
    'httpx',  # connect with the internet in general
]


setup(
    name='teleflask', version="3.0.0.dev1",
    description='Easily create Telegram bots with decorators functions, running a webserver of your choice. Webhooks made easy, but you don\'t even have to use \'em.',
    long_description=long_description,
    # The project's main homepage.
    url='https://github.com/luckydonald/teleflask',
    # Author details
    author='luckydonald',
    author_email='teleflask+code@luckydonald.de',
    # Choose your license
    license='GPLv3+',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta', # 2 - Pre-Alpha, 3 - Alpha, 4 - Beta, 5 - Production/Stable
        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Multimedia',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Framework :: Flask',
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.7',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
    ],
    # What does your project relate to?
    keywords='pytgbot flask webhook telegram bot api python message send receive python secure fast answer reply image voice picture location contacts typing multi messanger inline quick reply gif image video mp4 mpeg4 webserver decorators',
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['teleflask', 'teleflask.server'],
    # packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    # List run-time dependencies here. These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'pprint',
        "DictObject", "luckydonald-utils>=0.70",  # general utils
        "python-magic", "backoff>=1.4.1",  # messages messages
        # backoff >=1.4.1 because of a bug with the flask development server
        # see https://github.com/litl/backoff/issues/30
        'pytgbot>=4.0" # connect to telegram'
    ],
    # List additional groups of dependencies here (e.g. development dependencies).
    # You can install these using the following syntax, for example:
    # $ pip install -e .[dev,test]
    extras_require = {
        'dev': ['bump2version'],
        'sync': SYNC_REQUIREMENTS,
        'async': ASYNC_REQUIREMENTS,
        'flask': [
            'flask',
        ] + SYNC_REQUIREMENTS,
        'quart': [
            'quart',
        ] + ASYNC_REQUIREMENTS,
        # 'test': ['coverage'],
    },
    # If there are data files included in your packages that need to be
    # installed, specify them here. If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    # 'sample': ['package_data.dat'],
    # },
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
)
