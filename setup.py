#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "attrs >= 16.0",
    "typing >= 3.5.2; python_version<'3.5'",
    "singledispatch >= 3.4.0.3; python_version<'3.4'",
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='cattrs',
    version='0.1.0',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
