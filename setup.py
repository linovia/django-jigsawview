#!/usr/bin/env python
"""
Django JigsawView
=================

:copyright: (c) 2012 by Linovia.
:license: BSD, see LICENSE for more details.
"""
from setuptools import setup, find_packages


tests_require = [
    'mock',
    'unittest2',
    'nose',
]

install_requires = [
    'six',
    'Django>=1.4',
    'django-filter',
]

setup(
    name='django-jigsawview',
    version='0.1.0',
    author='Xavier Ordoquy',
    author_email='xordoquy@linovia.com',
    url='https://github.com/linovia/django-jigsawview',
    description='An extended alternative to Django generic class based views.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    license='BSD',
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
    ],
)
