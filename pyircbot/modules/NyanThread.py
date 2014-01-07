#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook
import re
from time import time
from urllib import request
from bs4 import BeautifulSoup
from bs4.element import Tag as bs_type_tag

class NyanThread(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.check)]
		self.lastrun = 0
		self.pagepattern = re.compile(r'<a class="navPages" href="https:\/\/bitcointalk\.org\/index\.php\?topic=403335\.([0-9]+)">([0-9]+)</a>')
		self.messagepattern = re.compile(r'<span style="color: RED;">([^<]+)</span>', flags=re.IGNORECASE)
		self.linkmessage = re.compile(r'<a href="https:\/\/bitcointalk\.org\/index\.php\?topic=403335\.msg([0-9]+)#msg([0-9]+)">')
		
	def check(self,  args, prefix, trailing):
		if not args[0][0]=="#":
			return
		cmd = self.bot.messageHasCommand(".story", trailing)
		if cmd:
			if time() - self.lastrun < 10:
				return
			
			self.log.info("Nyanthread: fetching story...")
			prefixObj = self.bot.decodePrefix(prefix)
			page = request.urlopen("https://bitcointalk.org/index.php?topic=403335").read()
			pages = self.pagepattern.findall(page.decode("ISO-8859-1"))
			lastpage = pages[-1]
			lastpagelink = "https://bitcointalk.org/index.php?topic=403335.%s" % lastpage[0]
			self.log.info("Nyanthread: last page is %s" % lastpagelink)
			page = request.urlopen(lastpagelink).read()
			
			bs = BeautifulSoup(page)
			
			body = bs.find('div', id="bodyarea")
			thread = body.find('form', id="quickModForm")
			posttable = thread.find('table', class_="bordercolor")
			
			postTrs = []
			for item in posttable:
				postTrs.append(item)
			
			postTrs.reverse()
			
			for item in postTrs:
				if type(item) == bs_type_tag:
					message = item.find('div', class_="post")
					if message:
						redContent = self.messagepattern.findall(message.decode_contents())
						if len(redContent)>0:
							linkmessage = self.linkmessage.findall(item.decode_contents())
							lastpagelink = "https://bitcointalk.org/index.php?topic=403335.msg%s#msg%s"%(linkmessage[0][0],linkmessage[0][0])
							if len(linkmessage)>75:
								continue
							self.bot.act_PRIVMSG(args[0], "%s: %s - %s" % (prefixObj.nick, redContent[0], lastpagelink))
							self.lastrun = time()
							return
			
			self.bot.act_PRIVMSG(args[0], "%s: failed to read thread :(" % (prefixObj.nick))
			self.lastrun = time()
			return
