from modulebase import ModuleBase,ModuleHook
import datetime
import time
import math

class Calc(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		
		self.hooks=[ModuleHook("PRIVMSG", self.calc)]
		self.timers={}
		
		self.sqlite = self.bot.getBestModuleForService("sqlite")
		if self.sqlite==None:
			self.log.error("Calc: SQLIite service is required.")
			return
		
		self.sql = self.sqlite.opendb("calc.db")
		
		if not self.sql.tableExists("calc_addedby"):
			c = self.sql.getCursor()
			c.execute("""
				CREATE TABLE `calc_addedby` (
				  `id` INTEGER PRIMARY KEY,
				  `username` varchar(32),
				  `userhost` varchar(128)
				) ;
			""")
			c.close()
		if not self.sql.tableExists("calc_channels"):
			c = self.sql.getCursor()
			c.execute("""
				CREATE TABLE `calc_channels` (
				  `id` INTEGER PRIMARY KEY,
				  `channel` varchar(32)
				) ;
			""")
		if not self.sql.tableExists("calc_definitions"):
			c = self.sql.getCursor()
			c.execute("""
				CREATE TABLE `calc_definitions` (
				  `id` INTEGER PRIMARY KEY,
				  `word` INTEGET,
				  `definition` varchar(512),
				  `addedby` INTEGER,
				  `date` timestamp,
				  `status` varchar(16)
				) ;
			""")
		if not self.sql.tableExists("calc_words"):
			c = self.sql.getCursor()
			c.execute("""
				CREATE TABLE `calc_words` (
				  `id` INTEGER PRIMARY KEY,
				  `channel` INTEGER,
				  `word` varchar(512),
				  `status` varchar(32),
				  unique(`channel`,`word`)
				);
			""")
			c.close()
	
	def timeSince(self, channel, timetype):
		if not channel in self.timers:
			self.createDefaultTimers(channel)
		return time.time()-self.timers[channel][timetype]
	
	def updateTimeSince(self, channel, timetype):
		if not channel in self.timers:
			self.createDefaultTimers(channel)
		self.timers[channel][timetype] = time.time()
	
	def createDefaultTimers(self, channel):
		self.timers[channel]={"add":0, "calc":0, "calcspec":0, "match":0}
	
	def remainingToStr(self, total, elasped):
		remaining = total-elasped
		minutes = int(math.floor(remaining/60))
		seconds = int(remaining - (minutes*60))
		return "Please wait %s minute(s) and %s second(s)." % (minutes, seconds)
	
	def calc(self, args, prefix, trailing):
		# Channel only
		if not args[0][0]=="#":
			return
		sender = self.bot.decodePrefix(prefix)
		
		foundCalc = False
		commandFound = ""
		for cmd in self.config["cmd_calc"]:
			if trailing[0:len(cmd)] == cmd and ( len(trailing) == len(cmd) or (trailing[len(cmd):len(cmd)+1] in [" ", "="])):
				commandFound=cmd
				foundCalc=True
			
		if foundCalc:
			calcCmd = trailing[len(cmd)-1:].strip()
			if "=" in calcCmd[1:]:
				" Add a new calc "
				calcWord, calcDefinition = calcCmd.split("=", 1)
				calcWord = calcWord.strip()
				calcDefinition = calcDefinition.strip()
				if self.config["allowDelete"] and calcDefinition == "":
					result = self.deleteCalc(args[0], calcWord)
					if result:
						self.bot.act_PRIVMSG(args[0], "Calc deleted, %s." % sender.nick)
					else:
						self.bot.act_PRIVMSG(args[0], "Sorry %s, I don't know what '%s' is." % (sender.nick, calcWord))
				else:
					if self.config["delaySubmit"]>0 and self.timeSince(args[0], "add") < self.config["delaySubmit"]:
						self.bot.act_PRIVMSG(sender.nick, self.remainingToStr(self.config["delaySubmit"], self.timeSince(args[0], "add")))
					else:
						self.addNewCalc(args[0], calcWord, calcDefinition, prefix)
						self.bot.act_PRIVMSG(args[0], "Thanks for the info, %s." % sender.nick)
						self.updateTimeSince(args[0], "add")
			elif len(calcCmd)>0:
				" Lookup the word in calcCmd "
				
				if self.config["delayCalcSpecific"]>0 and self.timeSince(args[0], "calcspec") < self.config["delayCalcSpecific"]:
					self.bot.act_PRIVMSG(sender.nick, self.remainingToStr(self.config["delayCalcSpecific"], self.timeSince(args[0], "calcspec")))
				else:
					randCalc = self.getSpecificCalc(args[0], calcCmd)
					if randCalc==None:
						self.bot.act_PRIVMSG(args[0], "Sorry %s, I don't know what '%s' is." % (sender.nick, calcCmd))
					else:
						self.bot.act_PRIVMSG(args[0], "%s \x03= %s \x0314[added by: %s]" % (randCalc["word"], randCalc["definition"], randCalc["by"]))
						self.updateTimeSince(args[0], "calcspec")
			else:
				if self.config["delayCalc"]>0 and self.timeSince(args[0], "calc") < self.config["delayCalc"]:
					self.bot.act_PRIVMSG(sender.nick, self.remainingToStr(self.config["delayCalc"], self.timeSince(args[0], "calc")))
				else:
					randCalc = self.getRandomCalc(args[0])
					if randCalc == None:
						self.bot.act_PRIVMSG(args[0], "This channel has no calcs, %s :(" % (sender.nick,))
					else:
						self.bot.act_PRIVMSG(args[0], "%s \x03= %s \x0314[added by: %s]" % (randCalc["word"], randCalc["definition"], randCalc["by"]))
						self.updateTimeSince(args[0], "calc")
			return
		
		cmd = self.bot.messageHasCommand(self.config["cmd_match"], trailing, True)
		if cmd:
			if self.config["delayMatch"]>0 and self.timeSince(args[0], "match") < self.config["delayMatch"]:
				self.bot.act_PRIVMSG(sender.nick, self.remainingToStr(self.config["delayMatch"], self.timeSince(args[0], "match")))
			else:
				term = cmd.args_str
				if term.strip()=='':
					return
				c = self.sql.getCursor()
				channelId = self.getChannelId(args[0])
				c.execute("SELECT * FROM `calc_words` WHERE `word` LIKE ? AND `channel`=? ORDER BY `word` ASC ;", ("%%"+term+"%%", channelId))
				rows = c.fetchall()
				if len(rows)==0:
					self.bot.act_PRIVMSG(args[0], "%s: Sorry, no matches" % sender.nick)
				else:
					matches = []
					for row in rows[0:10]:
						if row == None:
							break
						matches.append(row["word"])
					self.bot.act_PRIVMSG(args[0], "%s: %s match%s (%s\x03)" % (sender.nick, len(matches), "es" if len(matches)>1 else "", ", \x03".join(matches) ))
					self.updateTimeSince(args[0], "match")
				
	def addNewCalc(self, channel, word, definition, prefix):
		sender = self.bot.decodePrefix(prefix)
		
		" Find the channel ID"
		channelId = self.getChannelId(channel)
		
		" Check if we need to add a user"
		c = self.sql.getCursor()
		name = sender.nick
		host = sender.hostname
		c.execute("SELECT * FROM `calc_addedby` WHERE `username`=? AND `userhost`=? ;", (name, host))
		rows = c.fetchall()
		if len(rows)==0:
			c.execute("INSERT INTO `calc_addedby` (`username`, `userhost`) VALUES (?, ?) ;", (name, host,))
			c.execute("SELECT * FROM `calc_addedby` WHERE `username`=? AND `userhost`=? ;", (name, host))
			rows = c.fetchall()
		addedId = rows[0]["id"]
		
		" Check if the word exists"
		c.execute("SELECT * FROM `calc_words` WHERE `channel`=? AND `word`=? ;", (channelId, word))
		rows = c.fetchall()
		if len(rows)==0:
			c.execute("INSERT INTO `calc_words` (`channel`, `word`, `status`) VALUES (?, ?, ?) ;", (channelId, word, 'approved'))
			c.execute("SELECT * FROM `calc_words` WHERE `channel`=? AND `word`=? ;", (channelId, word))
			rows = c.fetchall()
		wordId = rows[0]["id"]
		" Add definition "
		c.execute("INSERT INTO `calc_definitions` (`word`, `definition`, `addedby`, `date`, `status`) VALUES (?, ?, ?, ?, ?) ;", (wordId, definition, addedId, datetime.datetime.now(), 'approved',))
		c.close()
		pass
	
	def getSpecificCalc(self, channel, word):
		c = self.sql.getCursor()
		channelId = self.getChannelId(channel)
		c.execute("SELECT `cw`.`word`, (SELECT `cdq`.`id` FROM `calc_definitions` `cdq` WHERE `cdq`.`word`=`cw`.`id` AND `cdq`.`status`='approved' ORDER BY `cdq`.`date` DESC LIMIT 1) as `definitionId` FROM `calc_words` `cw` WHERE `cw`.`channel`=? AND `cw`.`status`='approved' AND `cw`.`word`=? COLLATE NOCASE ORDER BY RANDOM() LIMIT 1 ;", (channelId, word.lower()))
		word = c.fetchone()
		
		if word == None:
			return None
		
		c.execute("SELECT `ca`.`username`, `cd`.`definition` FROM `calc_definitions` `cd` JOIN `calc_addedby` `ca` ON `ca`.`id` = `cd`.`addedby` WHERE `cd`.`id`=? LIMIT 1 ;", (word["definitionId"], ))
		
		who = c.fetchone()
		
		if who == None:
			return None
		
		c.close()
		return {"word":word["word"], "definition":who["definition"], "by":who["username"]}
		
	
	def getRandomCalc(self, channel):
		c = self.sql.getCursor()
		channelId = self.getChannelId(channel)
		
		for i in range(0, 5):
			c.execute("SELECT `cw`.`word`, (SELECT `cdq`.`id` FROM `calc_definitions` `cdq` WHERE `cdq`.`word`=`cw`.`id` AND `cdq`.`status`='approved' ORDER BY `cdq`.`date` DESC LIMIT 1) as `definitionId` FROM `calc_words` `cw` WHERE `cw`.`channel`=? AND `cw`.`status`='approved' ORDER BY RANDOM() LIMIT 1 ;", (channelId,))
			word = c.fetchone()
			if word == None:
				return None
			c.execute("SELECT `ca`.`username`, `cd`.`definition` FROM `calc_definitions` `cd` JOIN `calc_addedby` `ca` ON `ca`.`id` = `cd`.`addedby` WHERE `cd`.`id`=? LIMIT 1 ;", (word["definitionId"], ))
			
			who = c.fetchone()
			
			if who == None:
				continue
			
			c.close()
			return {"word":word["word"], "definition":who["definition"], "by":who["username"]}
	
	def deleteCalc(self, channel, word):
		" Return true if deleted something, false if it doesnt exist"
		c = self.sql.getCursor()
		channelId = self.getChannelId(channel)
		c.execute("SELECT * FROM `calc_words` WHERE `channel`=? and `word`=? ;", (channelId, word))
		rows = c.fetchall()
		if len(rows)==0:
			c.close()
			return False
		
		wordId = rows[0]["id"]
		
		#c.execute("DELETE FROM `calc_words` WHERE `id`=? ;", (wordId,))
		#c.execute("DELETE FROM `calc_definitions` WHERE `word`=? ;", (wordId,))
		c.execute("UPDATE `calc_definitions` SET `status`='deleted' WHERE `word`=? ;", (wordId,))
		
		c.close()
		return True
	
	def getChannelId(self, channel):
		c = self.sql.getCursor()
		c.execute("SELECT * FROM `calc_channels` WHERE `channel` = ?", (channel,))
		rows = c.fetchall()
		if len(rows)==0:
			c.execute("INSERT INTO `calc_channels` (`channel`) VALUES (?);", (channel,))
			c.execute("SELECT * FROM `calc_channels` WHERE `channel` = ?", (channel,))
			rows = c.fetchall()
		chId = rows[0]["id"]
		c.close()
		return chId
