#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook

class PingResponder(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PING", self.pingrespond)]
	def pingrespond(self, args, prefix, trailing):
		# got a ping? send it right back
		self.bot.act_PONG(trailing)
		self.log.info("Responded to a ping: %s" % trailing)
