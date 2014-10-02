"""
.. module:: Error
	:synopsis: Module to deliberately cause an error for testing handling.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook

class Error(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName)
		self.hooks=[ModuleHook("PRIVMSG", self.error)]
	
	def error(self, args, prefix, trailing):
		if "error" in trailing:
			print(10/0)

