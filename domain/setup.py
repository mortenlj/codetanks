#!/usr/bin/env python

from setuptools import setup
import re


def read(filename):
    f = open(filename)
    contents = f.read()
    f.close()
    return contents


def parse_requirements(file_name):
    requirements = []
    for line in read(file_name).split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)
    return requirements


setup(
    name="Codetanks Domain",
    version="0.1",
    packages=["ibidem", "ibidem.codetanks", "ibidem.codetanks.domain"],
    package_dir={
        '': 'build/python'
    },
    install_requires=parse_requirements("requirements.txt"),
    namespace_packages=["ibidem", "ibidem.codetanks"],
    zip_safe=True,
    test_suite="nose.collector",

    # Metadata
    author="Morten Lied Johansen",
    author_email="mortenjo@ifi.uio.no",
    license="LGPL",
    keywords="ibidem codetanks",
    url="https://bitbucket.org/mortenlj/codetanks",
)
