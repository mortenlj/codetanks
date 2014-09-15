#!/usr/bin/env python

from setuptools import setup, Command
import os
import re


class Thrift(Command):
    description = "Compile Thrift IDL into python source"
    user_options = []

    def initialize_options(self):
        self.thrift_file = os.path.join("thrift", "messages.thrift")

    def finalize_options(self):
        pass

    def run(self):
        self.spawn(["thrift-0.9.1", "-strict", "-verbose", "--gen", "py:new_style,utf8strings,slots", "-o", "src", self.thrift_file])
        path = "."
        for folder in ("src", "gen-py", "ibidem", "codetanks"):
            path = os.path.join(path, folder)
            filename = os.path.join(path, "__init__.py")
            if os.path.exists(filename):
                with open(filename, "w") as fobj:
                    fobj.write("__import__('pkg_resources').declare_namespace(__name__)\n")
        os.unlink(os.path.join("src", "gen-py", "__init__.py"))


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
        '': 'src/gen-py'
    },
    install_requires=parse_requirements("requirements.txt"),
    namespace_packages=["ibidem", "ibidem.codetanks"],
    zip_safe=True,
    cmdclass={"thrift": Thrift},

    # Metadata
    author="Morten Lied Johansen",
    author_email="mortenjo@ifi.uio.no",
    license="LGPL",
    keywords="ibidem codetanks",
    url="https://bitbucket.org/mortenlj/codetanks",
)
