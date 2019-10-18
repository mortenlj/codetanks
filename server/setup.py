#!/usr/bin/env python

from __future__ import print_function

import os
import subprocess
import sys
from distutils.cmd import Command
from distutils.spawn import find_executable

from setuptools import setup


class ThriftBuild(Command):
    description = "Compile thrift sources"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def find_thrift(self):
        if 'THRIFT' in os.environ and os.path.exists(os.environ['THRIFT']):
            thrift = os.environ['THRIFT']
        else:
            thrift = find_executable('thrift')

        if thrift is None:
            sys.stderr.write('thrift not found. Is thrift-compiler installed? \n'
                             'Alternatively, you can point the THRIFT environment variable at a local version.')
            sys.exit(1)
        self.debug_print("Thrift compiler found: %s" % thrift)
        return thrift

    def run(self):
        self.announce("Generating thrift code")
        source = os.path.join(os.path.dirname(__file__), "..", "domain", "thrift", "messages.thrift")
        self.debug_print("Compiling thrift source %r" % source)
        subprocess.check_call(
            [self.find_thrift(), "-verbose", "-out", ".", "--gen", "py:new_style,utf8strings,slots", source])


setup(
    name="codetanks-server",
    version="0.5",
    packages=[
        "ibidem",
        "ibidem.codetanks",
        "ibidem.codetanks.domain",
        "ibidem.codetanks.server"
    ],
    install_requires=[
        "setuptools",
        "pyzmq",
        "pinject",
        # "-e hg+https://bitbucket.org/mortenlj/euclid#egg=euclid-ng", # TODO: Must be installed using pip?
    ],
    namespace_packages=["ibidem", "ibidem.codetanks"],
    zip_safe=True,
    tests_require=[
        "pytest",
        "mock",
        "PyHamcrest",
    ],
    setup_requires=["pytest-runner"],

    # Metadata
    author="Morten Lied Johansen",
    author_email="mortenjo@ifi.uio.no",
    license="LGPL",
    keywords="ibidem codetanks",
    url="https://bitbucket.org/mortenlj/codetanks",

    # Entry points
    entry_points={
        "console_scripts": [
            "codetanks = ibidem.codetanks.server.main:main",
            "codetanks_bot = ibidem.codetanks.server.cli_bot:main"
        ],
    },
    cmdclass={"build_thrift": ThriftBuild}
)
