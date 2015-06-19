#!/usr/bin/env python3
from setuptools import setup

setup(name='pyircbot',
	version='4.0.0aa',
	description='A modular python irc bot',
	url='http://gitlab.xmopx.net/dave/pyircbot3/tree/master',
	author='dpedu',
	author_email='dave@davepedu.com',
	packages=['pyircbot'],
	scripts=['bin/pyircbot'],
	zip_safe=False)
