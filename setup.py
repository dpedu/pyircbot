#!/usr/bin/env python3
from setuptools import setup

__version__ = "4.0.0-r03"

setup(name='pyircbot',
      version='4.0.0-r03',
      description='A modular python irc bot',
      url='http://gitlab.xmopx.net/dave/pyircbot3/tree/master',
      author='dpedu',
      author_email='dave@davepedu.com',
      packages=['pyircbot', 'pyircbot.modules'],
      entry_points={
          "console_scripts": [
              "pyircbot = pyircbot.cli:main",
              "pubsubbot = pyircbot.clipub:main"
          ]
      },
      zip_safe=False)
