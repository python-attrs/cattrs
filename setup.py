#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "attrs >= 17.3",
    "functools32 >= 3.2.3; python_version<'3.0'",
    "singledispatch >= 3.4.0.3; python_version<'3.0'",
    "enum34 >= 1.1.6; python_version<'3.0'",
    "typing >= 3.5.3; python_version<'3.0'",
]

setup(
    name='cattrs',
    version='0.8.0',
    description="Composable complex class support for attrs.",
    long_description=readme + '\n\n' + history,
    author="Tin Tvrtković",
    author_email='tinchester@gmail.com',
    url='https://github.com/Tinche/cattrs',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='cattrs',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
