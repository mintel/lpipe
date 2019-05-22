#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import find_packages, setup

HERE = os.path.dirname(os.path.abspath(__file__))

# Read title, version etc from _version.py and put them into local scope
exec(open("pypedream/_version.py").read())


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


def list_requirements(filename):
    return [line.strip() for line in open(filename) if line.strip() and line[0] != "-"]


setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    maintainer=__author__,
    maintainer_email=__author_email__,
    license="MIT",
    url=__uri__,
    packages=find_packages(where=HERE, exclude=["tests"]),
    description=__summary__,
    long_description=read("README.md"),
    py_modules=["pytest_everest"],
    setup_requires=["pytest-runner"],
    tests_require=list_requirements("requirements-dev.txt"),
    python_requires=">=3.4",
    install_requires=list_requirements("requirements.txt"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["everest = pytest_everest"]},
)
