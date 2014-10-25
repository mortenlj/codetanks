#!/usr/bin/env python

import shutil

from setuptools import setup, Command
import os
import re


class Thrift(Command):
    description = "Compile Thrift IDL into python source"
    user_options = []

    _languages = [
        "py:new_style,utf8strings,slots"
    ]

    def initialize_options(self):
        self.thrift_file = os.path.join("thrift", "messages.thrift")

    def finalize_options(self):
        pass

    def _fixup_py(self):
        path = "."
        for folder in ("target", "gen-py", "ibidem", "codetanks"):
            path = os.path.join(path, folder)
            filename = os.path.join(path, "__init__.py")
            if os.path.exists(filename):
                with open(filename, "w") as fobj:
                    fobj.write("__import__('pkg_resources').declare_namespace(__name__)\n")
        os.unlink(os.path.join("target", "gen-py", "__init__.py"))

    def run(self):
        gen_py_path = os.path.join("target", "gen-py")
        os.makedirs(gen_py_path)
        shutil.rmtree(gen_py_path)
        shutil.copytree(os.path.join("src", "python", "ibidem"), os.path.join("target", "gen-py", "ibidem"))
        cmd_args = ["thrift-0.9.1", "-strict", "-verbose"]
        for lang in self._languages:
            cmd_args.append("--gen")
            cmd_args.append(lang)
        cmd_args.extend(["-o", "target", self.thrift_file])
        self.spawn(cmd_args)
        self._fixup_py()


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
        '': 'target/gen-py'
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
