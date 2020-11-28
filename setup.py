#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "attrs >= 20.1.0",
]

dev_reqs = [
    "bumpversion",
    "wheel",
    "watchdog",
    "flake8",
    "tox",
    "coverage",
    "Sphinx",
    "pytest",
    "hypothesis",
    "pendulum",
    "isort",
    "black",
]

setup(
    name="cattrs",
    version="1.1.2",
    description="Composable complex class support for attrs.",
    long_description=readme + "\n\n" + history,
    author="Tin Tvrtković",
    author_email="tinchester@gmail.com",
    url="https://github.com/Tinche/cattrs",
    packages=find_packages(where="src", exclude=["tests*"]),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=requirements,
    extras_require={"dev": dev_reqs},
    license="MIT license",
    zip_safe=False,
    keywords="cattrs",
    python_requires="~=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
