#!/usr/bin/env python3
from setuptools import setup

__version__ = "4.0.0-r02"

setup(name='pyircbot',
	version='4.0.0-r02',
	description='A modular python irc bot',
	url='http://gitlab.xmopx.net/dave/pyircbot3/tree/master',
	author='dpedu',
	author_email='dave@davepedu.com',
	packages=['pyircbot', 'pyircbot.modules'],
	scripts=['bin/pyircbot'],
	zip_safe=False)
