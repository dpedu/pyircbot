#!/usr/bin/env python

"""
.. module::TextCDC
	:synopsis: Text Chrisdotcode, right now.
.. moduleauthor::Nick Krichevsky <nick@ollien.com>
"""

import smtplib
import imaplib
from threading import Timer
from pyircbot.modulebase import ModuleBase, ModuleHook

class TextCDC(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName)
		self.hooks.append(ModuleHook("PRIVMSG",self.handleMessage))	
		self.loadConfig()
		self.timer = None
		self.setupTimer()

	def ondisable(self):
		if self.timer != None:
			self.timer.cancel()

	def handleMessage(self, args, prefix, trailing):
		channel = args[0]
		if self.bot.messageHasCommand(".textstatus", trailing):
			#self.bot.act_PRIVMSG(channel, "POP: %s" % "Good" if setupPop() != None else "Failed.")
			self.bot.act_PRIVMSG(channel, "SMTP: %s" % "Good" if setupSMTP() != None else "Failed.")
		if self.bot.messageHasCommand(".text-cdc", trailing):
			message = ' '.join(trailing.split(" ")[1:])
			smtp = self.setupSMTP()
			try:
				smtp.sendmail(self.config["account"]["auth"]["username"], self.config["email-addr"], "Subject:\n\n%s" % message)
				smtp.quit()
				self.bot.act_PRIVMSG(channel, "Message sent.")
			except Exception as e:
				self.bot.log.error(str(e))
				self.bot.act_PRIVMSG(channel, "An SMTP Error has Occured")

	def setupIMAP(self):
		imapObj = None
		if self.config["account"]["imap"]["ssl"]:
			imapObj = imaplib.IMAP4_SSL(self.config["account"]["imap"]["host"], self.config["account"]["imap"]["port"])
		else:
			imapObj = imaplib.IMAP4(self.config["account"]["imap"]["host"], self.config["account"]["imap"]["port"])
		imapObj.login(self.config["account"]["auth"]["username"], self.config["account"]["auth"]["password"])
		resp = imapObj.select("INBOX")
		if resp[0] == "OK":
			return imapObj
		else:
			return None

	def setupSMTP(self):
		smtpObj = None
		if self.config["account"]["smtp"]["ssl"]:
			smtpObj = smtplib.SMTP_SSL(self.config["account"]["smtp"]["host"], self.config["account"]["smtp"]["port"])	
		else:
			smtpObj = smtplib.SMTP_SSL(self.config["account"]["smtp"]["host"], self.config["account"]["smtp"]["port"])
		if self.config["account"]["smtp"]["authentication"]:
			resp = smtpObj.login(self.config["account"]["auth"]["username"], self.config["account"]["auth"]["password"])
			if resp[0] == 235:
				return smtpObj
			else:
				return None
		else:
			resp = smtpObj.connect()
			if resp[0] == 220:
				return smtpObj
			else:
				return None
	
	def setupTimer(self):
		self.timer = Timer(self.config["interval"], self.checkMail, [self.bot, self.config["email-addr"], self.config["output-channels"]],{})
		self.timer.start()
	
	def checkMail(self, bot, emailAddr, channels, imapObj = None):
		try:
			if imapObj == None:
				imapObj = self.setupIMAP()
			result = imapObj.search(None, "(FROM \"%s\")" % emailAddr)
			if (result[0] == "OK"):
				messageIds = result[1][0].decode("utf-8")
				if len(messageIds) > 0:
					messageIds = messageIds.split(" ")
					for messageId in messageIds:
						message = imapObj.fetch(messageId, "BODY[TEXT]")
						if (message[0] == "OK"):
							messageText = message[1][0][1].decode("utf-8").split("-----Original Message-----")[0].rstrip()
							for channel in channels: 
								bot.act_PRIVMSG(channel, "Message from CDC: %s" % messageText)
							imapObj.store(messageId, "+FLAGS", "\\Deleted")
						else:
							raise Exception("SMTP Error. Status was %s, expected OK" % message[0])
				imapObj.logout()
				self.setupTimer()
		except Exception as e:
			if imapObj != None:
				imapObj.logout()
			self.setupTimer()
			raise e	
