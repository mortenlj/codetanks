#!/usr/bin/env python


import os
import subprocess
import sys
from distutils.cmd import Command
from distutils.spawn import find_executable

from datetime import datetime

from setuptools import setup


class ProtoBuild(Command):
    description = "Compile protobuf sources"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def find_protoc(self):
        """Locates protoc executable"""

        if 'PROTOC' in os.environ and os.path.exists(os.environ['PROTOC']):
            protoc = os.environ['PROTOC']
        else:
            protoc = find_executable('protoc')

        if protoc is None:
            sys.stderr.write('protoc not found. Is protobuf-compiler installed? \n'
                             'Alternatively, you can point the PROTOC environment variable at a local version.')
            sys.exit(1)

        return protoc

    def run(self):
        proto_dir = os.path.join(os.path.dirname(__file__), "..", "domain", "protobuf")
        source = os.path.join(proto_dir, "messages.proto")
        output_dir = os.path.join(os.path.dirname(__file__), "ibidem", "codetanks", "domain")
        output = os.path.join(output_dir, "messages_pb2.py")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            with open(os.path.join(output_dir, "__init__.py"), "w"):
                pass

        if not os.path.exists(output) or (os.path.getmtime(source) > os.path.getmtime(output)):
            sys.stderr.write('Protobuf-compiling ' + source + '\n')
            subprocess.check_call([self.find_protoc(),
                                   '--python_out=%s' % output_dir,
                                   '--proto_path=%s' % proto_dir,
                                   source])
        else:
            sys.stderr.write("Proto file %s already generated at %s, pass\n" %
                             (output, datetime.fromtimestamp(os.path.getmtime(output))))


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
        "pygame",
        "fiaas-logging==0.1.1",
        "protobuf==3.13.0",
        # "euclid3>0.0.1", # TODO: Must be installed using pip?
    ],
    namespace_packages=["ibidem", "ibidem.codetanks"],
    zip_safe=True,
    tests_require=[
        "pytest",
        "mock",
    ],
    setup_requires=["pytest-runner"],

    # Metadata
    author="Morten Lied Johansen",
    author_email="mortenjo@ifi.uio.no",
    license="LGPL",
    keywords="ibidem codetanks",
    url="https://github.com/mortenlj/codetanks",

    # Entry points
    entry_points={
        "console_scripts": [
            "codetanks = ibidem.codetanks.server.main:main",
            "codetanks_bot = ibidem.codetanks.server.cli_bot:main"
        ],
    },
    cmdclass={
        "build_proto": ProtoBuild,
    }
)
