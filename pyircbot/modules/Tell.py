"""
.. module:: Tell
	:synopsis: Deliver a message to a user when they're next seen

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
import datetime
from time import mktime

class Tell(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		
		self.db = None
		serviceProviders = self.bot.getmodulesbyservice("sqlite")
		if len(serviceProviders)==0:
			self.log.error("Tell: Could not find a valid sqlite service provider")
		else:
			self.log.info("Tell: Selecting sqlite service provider: %s" % serviceProviders[0])
			self.db = serviceProviders[0].opendb("tell.db")
		
		if not self.db.tableExists("tells"):
			self.log.info("Remind: Creating table: tells")
			c = self.db.query("""CREATE TABLE IF NOT EXISTS `tells` (
			`id` INTEGER PRIMARY KEY,
			`sender` varchar(64),
			`channel` varchar(64),
			`when` INTEGER,
			`recip` varchar(64),
			`message` varchar(2048)
			) ;""").close()
		
		# Purge expired tells
		self.db.query("DELETE FROM `tells` WHERE `when`<?", (int(mktime(datetime.datetime.now().timetuple()))-self.config["maxage"],)).close()
		
		self.hooks=[
			ModuleHook(["JOIN", "PRIVMSG"], self.showtell),
			ModuleHook(["PRIVMSG"], self.tellcmds)
		]
	
	def showtell(self, args, prefix, trailing):
		#print("%s - %s - %s" % (args, prefix, trailing))
		prefix = self.bot.decodePrefix(prefix)
		
		# Look for tells for this person
		c = self.db.query("SELECT * FROM `tells` WHERE `recip`=?", (prefix.nick,))
		tells = c.fetchall()
		c.close()
		for tell in tells:
			agostr = Tell.timesince(datetime.datetime.fromtimestamp(tell["when"]))
			recip = None
			if tell["channel"]=="":
				recip = prefix.nick
			else:
				recip = tell["channel"]
			self.bot.act_PRIVMSG(recip, "%s: %s said %s ago: %s" % (
				prefix.nick,
				tell["sender"],
				agostr,
				tell["message"]
			))
			# Delete
			self.db.query("DELETE FROM `tells` WHERE `id`=?", (tell["id"],))
	
	def tellcmds(self, args, prefix, trailing):
		prefixObj = self.bot.decodePrefix(prefix)
		replyTo = prefixObj.nick if not "#" in args[0] else args[0]
		
		cmd = self.bot.messageHasCommand(".tell", trailing)
		if cmd:
			if len(cmd.args)<2:
				self.bot.act_PRIVMSG(replyTo, "%s: .tell <person> <message> - Tell someone something the next time they're seen. Example: .tell antiroach Do your homework!" % prefixObj.nick)
				return
			
			recip = cmd.args[0]
			message = ' '.join(cmd.args[1:]).strip()
			
			if message=="":
				self.bot.act_PRIVMSG(replyTo, "%s: .tell <person> <message> - Tell someone something the next time they're seen. Example: .tell antiroach Do your homework!" % prefixObj.nick)
				return
			
			self.db.query("INSERT INTO `tells` (`sender`, `channel`, `when`, `recip`, `message`) VALUES (?, ?, ?, ?, ?);",
				(
					prefixObj.nick,
					args[0] if "#" in args[0] else "",
					int(mktime(datetime.datetime.now().timetuple())),
					recip,
					message
				)
			).close()
			
			self.bot.act_PRIVMSG(replyTo, "%s: I'll pass that along." % prefixObj.nick)
	
	# Copyright (c) Django Software Foundation and individual contributors.
	# All rights reserved.
	#
	# Redistribution and use in source and binary forms, with or without
	# modification, are permitted provided that the following conditions are met:
	#
	#  1. Redistributions of source code must retain the above copyright notice,
	#	 this list of conditions and the following disclaimer.
	#
	#  2. Redistributions in binary form must reproduce the above copyright
	#	 notice, this list of conditions and the following disclaimer in the
	#	 documentation and/or other materials provided with the distribution.
	#
	#  3. Neither the name of Django nor the names of its contributors may be used
	#	 to endorse or promote products derived from this software without
	#	 specific prior written permission.
	#
	#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"AND
	#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
	#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
	#DISCLAIMED.IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
	#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
	#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
	#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
	#ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
	#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
	
	@staticmethod
	def timesince(d, now=None):
		"""
		Takes two datetime objects and returns the time between d and now
		as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
		then "0 minutes" is returned.
	
		Units used are years, months, weeks, days, hours, and minutes.
		Seconds and microseconds are ignored.  Up to two adjacent units will be
		displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
		possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.
	
		Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
		"""
		chunks = (
		  (60 * 60 * 24 * 365, ('year', 'years')),
		  (60 * 60 * 24 * 30, ('month', 'months')),
		  (60 * 60 * 24 * 7, ('week', 'weeks')),
		  (60 * 60 * 24, ('day', 'days')),
		  (60 * 60, ('hour', 'hours')),
		  (60, ('minute', 'minutes'))
		)
	
		# Convert int or float (unix epoch) to datetime.datetime for comparison
		if isinstance(d, int) or isinstance(d, float):
			d = datetime.datetime.fromtimestamp(d)
	
		# Convert datetime.date to datetime.datetime for comparison.
		if not isinstance(d, datetime.datetime):
			d = datetime.datetime(d.year, d.month, d.day)
		if now and not isinstance(now, datetime.datetime):
			now = datetime.datetime(now.year, now.month, now.day)
	
		if not now:
			now = datetime.datetime.now()
	
		# ignore microsecond part of 'd' since we removed it from 'now'
		delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
		since = delta.days * 24 * 60 * 60 + delta.seconds
		if since <= 0:
			# d is in the future compared to now, stop processing.
			return u'0 ' + 'minutes'
		for i, (seconds, name) in enumerate(chunks):
			count = since // seconds
			if count != 0:
				break
	
		if count == 1:
			s = '%(number)d %(type)s' % {'number': count, 'type': name[0]}
		else:
			s = '%(number)d %(type)s' % {'number': count, 'type': name[1]}
	
		if i + 1 < len(chunks):
			# Now get the second item
			seconds2, name2 = chunks[i + 1]
			count2 = (since - (seconds * count)) // seconds2
			if count2 != 0:
				if count2 == 1:
					s += ', %d %s' % (count2, name2[0])
				else:
					s += ', %d %s' % (count2, name2[1])
		return s
	
	@staticmethod
	def timeuntil(d, now=None):
		"""
		Like timesince, but returns a string measuring the time until
		the given time.
		"""
		if not now:
			now = datetime.datetime.now()
		return timesince(now, d)
