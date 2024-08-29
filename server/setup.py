#!/usr/bin/env python


from setuptools import setup

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
        "protobuf==5.28.0",
        # "euclid3>0.0.1", # TODO: Must be installed using pip?
    ],
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
    }
)
