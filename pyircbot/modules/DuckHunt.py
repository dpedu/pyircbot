#!/usr/bin/env python
"""
.. module:: DuckHunt
	:synopsis: An animal hunting IRC game

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from modulebase import ModuleBase,ModuleHook
import time
import yaml
import random
from threading import Timer
import os

class DuckHunt(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.hunt)]
		self.loadConfig()
		
		self.ymlPath = self.getFilePath("scores.yml")
		
		self.timer = None
		self.isDuckOut = False
		self.outStart = 0
		self.misses = {}
		
		self.startHunt()
	
	def hunt(self, args, prefix, trailing):
		prefixObj = self.bot.decodePrefix(prefix)
		fromWho = prefixObj.nick
		
		cmd = self.bot.messageHasCommand("!huntscore", trailing, False)
		if cmd:
			scores = self.loadScores()
			if not fromWho in scores:
				self.bot.act_PRIVMSG(fromWho, "You have no points :(")
			else:
				scores = scores[fromWho]
				kills = 0
				runts = 0
				prime = 0
				weight = 0.0
				shots = 0
				misses = 0
				for kill in scores:
					if kill["prime"]:
						prime+=1
					if kill["runt"]:
						runts+=1
					kills+=1
					weight+=kill["weight"]
					shots+=1
					shots+=kill["misses"]
					misses+=kill["misses"]
					
				self.bot.act_PRIVMSG(fromWho, "You've shot %s %s for a total weight of %s lbs." % (kills, self.config["animalSpeciesPlural"], weight))
				self.bot.act_PRIVMSG(fromWho, "%s prime catches, %s runts, %s bullets used and %s misses." % (prime, runts, shots, misses))
				#self.bot.act_PRIVMSG(fromWho, "More info & highscores: http://duckhunt.xmopx.net/")
				self.log.info("DuckHunt: %s used !huntscore" % fromWho)
			return
		
		# Channel only
		if not args[0][0]=="#":
			return
		
		cmd = self.bot.messageHasCommand("!shoot", trailing, False)
		if cmd:
			if self.isDuckOut:
				
				if not fromWho in self.misses:
					self.misses[fromWho]=0
					
				shotIn = round(time.time() - self.outStart, 2)
				
				if random.randint(0, 100) <= self.config["missChance"]:
					self.bot.act_PRIVMSG(self.config["activeChannel"], "%s fires after %s seconds and misses!" % (fromWho, shotIn))
					self.misses[fromWho]+=1
					return
				
				self.isDuckOut = False
				
				bagged = {
					"species":self.config["animalSpecies"],
					"gender":"M" if random.randint(0,1)==1 else "F",
					"time":shotIn,
					"prime":False,
					"runt":False,
					"weight":0.0,
					"date":time.time(),
					"misses":self.misses[fromWho]
				}
				
				message = "%s %s " % (fromWho, "bags")
				
				if random.randint(0, 100) <= self.config["primeChance"]:
					bagged["prime"]=True
					bagged["weight"]=self.getRandWeight(self.config["weightMax"], self.config["weightFat"])
					message += "a prime catch, a "
				elif random.randint(0, 100) <= self.config["runtChance"]:
					bagged["runt"]=True
					bagged["weight"]=self.getRandWeight(self.config["weightRunt"], self.config["weightMin"])
					message += "a runt of a catch, a "
				else:
					bagged["weight"]=self.getRandWeight(self.config["weightMin"], self.config["weightMax"])
					message += "a "
				
				message += "%s lb " % (bagged["weight"])
				if bagged["gender"]=="M":
					message += self.config["animalNameMale"]+" "
				else:
					message += self.config["animalNameFemale"]+" "
				
				message += "in %s seconds!" % shotIn
				self.bot.act_PRIVMSG(self.config["activeChannel"], message)
				
				self.addKillFor(fromWho, bagged)
				
				self.misses = {}
				
				self.startHunt();
	
	
	def startHunt(self):
		" Creates a timer that waits a certain amount of time then sends out a bird \_o< quack"
		delay = self.config["delayMin"] + random.randint(0, self.config["delayMax"]-self.config["delayMin"])
		self.timer = Timer(delay, self.duckOut)
		self.timer.start()
		print("DuckHunt: Sending out animal in %s seconds" % delay)
	
	def duckOut(self):
		self.isDuckOut = True
		self.bot.act_PRIVMSG(self.config["activeChannel"], self.config["animal"])
		self.outStart = time.time()
	
	def getRandWeight(self, minW, maxW):
		weight = maxW-minW;
		weight = float(weight)*random.random()
		return round(weight+minW, 2)
	
	def getScoreFor(self, playername):
		return 1
	
	def getScoresFor(self, playername):
		return 1
	
	def addKillFor(self, playername, kill):
		scores = self.loadScores()
		if scores==None:
			scores = {}
		if not playername in scores:
			scores[playername]=[]
		scores[playername].append(kill)
		self.saveScores(scores)
	
	def loadScores(self):
		if not os.path.exists(self.ymlPath):
			yaml.dump({}, open(self.ymlPath, 'w'))
		return yaml.load(open(self.ymlPath, 'r'))
	
	def saveScores(self, scores):
		yaml.dump(scores, open(self.ymlPath, 'w'))
	
	def ondisable(self):
		self.timer.cancel()
