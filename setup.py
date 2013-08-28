#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name = 'oadr2-ven',
    version = '0.1',
    description = 'OpenADR 2.0a VEN for Python',
    author = 'EnerNOC Advanced Technology',
    author_email = 'tnichols@enernoc.com',
    url = 'http://open.enernoc.com',
    packages = find_packages('.', exclude=['*.tests']),
    install_requires = ['lxml', 'sleekxmpp', 'dnspython', 'python-dateutil'],
    zip_safe = False,
)
