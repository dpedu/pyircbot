#!/ysr/bin/env python3

"""
.. module::LMGTFY
	:synopsis: LMGTFY
.. moduleauthor::Nick Krichevsky <nick@ollien.com>
"""

from pyircbot.modulebase import ModuleBase, ModuleHook

BASE_URL = "http://lmgtfy.com/?q="

class LMGTFY(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName)
		self.hooks.append(ModuleHook("PRIVMSG", self.handleMessage))
		self.bot = bot

	def handleMessage(self, args, prefix, trailing):
		channel = args[0]
		prefix = self.bot.decodePrefix(prefix)
		if self.bot.messageHasCommand(".lmgtfy", trailing):
			message = trailing.split(" ")[1:]
			link = self.createLink(message)
			self.bot.act_PRIVMSG(channel, "%s: %s" % (prefix.nick, link))
	
	def createLink(self, message):
		finalUrl = BASE_URL
		if type(message) == str:
			message = message.split(" ")

		for word in message:
			subs = {
				"@": "%40",
				"#": "%23",
				"$": "%24",
				"%": "%25",
				"^": "%26",
				"=": "%3D",
				"+": "%2B",
				"\\": "%5C",
				"/": "%2F",
				":": "%3A",
				";": "%3B",
				"'": "%27",
				"\"": "%28", 
				",": "%2C",
				"?": "%3F",
				"<": "%3C",
				">": "%3E",
				"[": "%5B", 
				"]": "%5D", 
				"{": "%7B",
				"}": "%7D",
				"|": "%7C",
				"`": "%60"
			}

			if word in subs:
				word = subs[word]

			finalUrl+=word
			if word != message[-1]:
				finalUrl+="+"

		return finalUrl
