#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from setuptools import setup, find_packages

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

VERSIONFILE = os.path.join(THIS_DIR, "web_dsl", "__init__.py")
VERSION = None
for line in open(VERSIONFILE, "r").readlines():
    if line.startswith("__version__"):
        VERSION = line.split('"')[1]

if not VERSION:
    raise RuntimeError("No version defined in web_dsl.__init__.py")


with open("requirements.txt") as f:
    required = [
        line.strip()
        for line in f.readlines()
        if line.strip() and not line.startswith("git+")
    ]


if sys.argv[-1].startswith("publish"):
    if os.system("pip list | grep wheel"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    if os.system("pip list | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    if sys.argv[-1] == "publishtest":
        os.system("twine upload -r test dist/*")
    else:
        os.system("twine upload dist/*")
        print("You probably want to also tag the version now:")
        print("  git tag -a {0} -m 'version {0}'".format(VERSION))
        print("  git push --tags")
    sys.exit()


setup(
    keywords="webdsl, domain-specific language, web application, web development",
    name="webdsl",
    packages=find_packages(include=["web_dsl", "web_dsl.*"]),
    include_package_data=True,
    install_requires=required,
    # test_suite="tests",
    url="https://github.com/giannisgkountras/web-dsl/",
    version=VERSION,
    zip_safe=False,
)
