#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "attrs >= 16.2",
]

if sys.version_info < (3, 0):
    requirements.extend([
        "functools32 >= 3.2.3; python_version<'3.0'",
        "singledispatch >= 3.4.0.3; python_version<'3.0'",
        # TODO: uncomment this for when vendor/python2/typing.py can be
        # removed. This will be for a version > 3.6.1 that has a fix that
        # allows singledispatch to work with parameterized generic types (cf
        # github/python/typing#405)
        #
        # "typing >= 3.5.3; python_version<'3.0'",
    ])


setup(
    name='cattrs',
    version='0.4.0dev0',
    description="Composable complex class support for attrs.",
    long_description=readme + '\n\n' + history,
    author="Tin Tvrtković",
    author_email='tinchester@gmail.com',
    url='https://github.com/Tinche/cattrs',
    packages=[
        'cattr',
    ],
    package_dir={'cattr':
                 'cattr'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='cattrs',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
)
