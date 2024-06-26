#!/usr/bin/env python

from setuptools import setup

setup(
    name="codetanks-viewer",
    version="0.5",
    packages=[
        "ibidem",
        "ibidem.codetanks",
        "ibidem.codetanks.domain",
        "ibidem.codetanks.viewer",
        "ibidem.codetanks.viewer.resources"
    ],
    package_data={
        'ibidem.codetanks.viewer.resources': ['*.png']
    },
    include_package_data=True,
    install_requires=[
        "pyzmq",
        "pygame>=2.0.0.dev12",
        "fiaas-logging==0.1.1",
        "six",
        "protobuf==5.27.2",
    ],
    zip_safe=True,

    # Metadata
    author="Morten Lied Johansen",
    author_email="mortenjo@ifi.uio.no",
    license="LGPL",
    keywords="ibidem codetanks",
    url="https://github.com/mortenlj/codetanks",

    # Entry points
    entry_points={
        "gui_scripts": [
            "codetanks-viewer = ibidem.codetanks.viewer.main:main"
        ],
    }
)
