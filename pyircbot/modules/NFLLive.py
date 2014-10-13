"""
.. module:: NFLLive
	:synopsis: Show upcoming NFL games and current scores.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from modulebase import ModuleBase,ModuleHook
from time import time
from requests import get
from lxml import etree
from datetime import datetime,timedelta

class NFLLive(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.cache = None
		self.cacheAge=0
		
		self.hooks=[ModuleHook(["PRIVMSG"], self.nflitup)]
	
	def nflitup(self, args, prefix, trailing):
		prefix = self.bot.decodePrefix(prefix)
		replyTo = prefixObj.nick if not "#" in args[0] else args[0]
		
		cmd = self.bot.messageHasCommand(".nfl", trailing)
		if cmd:
			games = self.getNflGamesCached()
			msg = []
			
			liveGames = []
			gamesLaterToday = []
			gamesToday = []
			gamesUpcoming = []
			gamesEarlierWeek = []
			
			# sort games
			for game in games["games"]:
				if not game["time"]==None:
					liveGames.append(game)
				elif game["quarter"]=="P" and game["startdate"].day==datetime.now().day:
					gamesLaterToday.append(game)
				elif game["startdate"].day==datetime.now().day:
					gamesToday.append(game)
				elif game["startdate"].day > datetime.now().day:
					gamesUpcoming.append(game)
				else:
					gamesEarlierWeek.append(game)
			
			# create list of formatted games
			liveGamesStr = []
			for game in liveGames:
				liveGamesStr.append(self.formatGameLive(game))
			liveGamesStr = ",   ".join(liveGamesStr)
			
			gamesLaterTodayStr = []
			for game in gamesLaterToday:
				gamesLaterTodayStr.append(self.formatGameFuture(game))
			gamesLaterTodayStr = ",   ".join(gamesLaterTodayStr)
			
			gamesTodayStr = []
			for game in gamesToday:
				gamesTodayStr.append(self.formatGamePast(game))
			gamesTodayStr = ",   ".join(gamesTodayStr)
			
			gamesUpcomingStr = []
			for game in gamesUpcoming:
				gamesUpcomingStr.append(self.formatGameFuture(game))
			gamesUpcomingStr = ",   ".join(gamesUpcomingStr)
			
			gamesEarlierWeekStr = []
			for game in gamesEarlierWeek:
				gamesEarlierWeekStr.append(self.formatGamePast(game))
			gamesEarlierWeekStr = ",   ".join(gamesEarlierWeekStr)
			
			msgPieces = []
			
			msgPieces.append("\x02NFL week %s\x02:" % (games["season"]["week"]))
			
			# Depending on args build the respon pieces
			if len(cmd.args)>0 and cmd.args[0]=="today":
				if not liveGamesStr == "":
					msgPieces.append("\x02Playing now:\x02 %s" % liveGamesStr)
				if not gamesLaterTodayStr == "":
					msgPieces.append("\x02Later today:\x02 %s" % gamesLaterTodayStr)
				if not gamesTodayStr == "":
					msgPieces.append("\x02Earlier today:\x02 %s" % gamesTodayStr)
			elif len(cmd.args)>0 and cmd.args[0]=="live":
				if not liveGamesStr == "":
					msgPieces.append("\x02Playing now:\x02 %s" % liveGamesStr)
			elif len(cmd.args)>0 and cmd.args[0]=="scores":
				if not liveGamesStr == "":
					msgPieces.append("\x02Playing now:\x02 %s" % liveGamesStr)
				if not gamesTodayStr == "":
					msgPieces.append("\x02Earlier today:\x02 %s" % gamesTodayStr)
				if not gamesEarlierWeekStr == "":
					msgPieces.append("\x02Earlier this week: \x02 %s" % gamesEarlierWeekStr)
			else:
				if not liveGamesStr == "":
					msgPieces.append("\x02Playing now:\x02 %s" % liveGamesStr)
				if not gamesLaterTodayStr == "":
					msgPieces.append("\x02Later today:\x02 %s" % gamesLaterTodayStr)
				if not gamesTodayStr == "":
					msgPieces.append("\x02Earlier today:\x02 %s" % gamesTodayStr)
				if not gamesEarlierWeekStr == "":
					msgPieces.append("\x02Earlier this week: \x02 %s" % gamesEarlierWeekStr)
				if not gamesUpcomingStr == "":
					msgPieces.append("\x02Upcoming:\x02 %s" % gamesUpcomingStr)
			
			# Collaspe the list into a repsonse string. Fix grammar
			msg = ",   ".join(msgPieces).replace(":,   ", ": ")
			
			# Nothing means there were probably no games
			if len(msgPieces)==1:
				msg = "No games!"
			
			if len(msg)>0:
				# The message can be long so chunk it into pieces splitting at commas
				while len(msg)>0:
					piece = msg[0:330]
					msg = msg[330:]
					while not piece[-1:]=="," and len(msg)>0:
						piece+=msg[0:1]
						msg = msg[1:]
					self.bot.act_PRIVMSG(replyTo, "%s: %s" % (prefix.nick, piece.strip()))
	
	def formatGameLive(self, game):
		c_vis = 3 if int(game["visitor_score"]) > int(game["home_score"]) else 4
		c_home = 4 if int(game["visitor_score"]) > int(game["home_score"]) else 3
		
		return "\x03%s%s(%s)\x03 @ \x03%s%s(%s)\x03 Q%s %s" % (
			c_vis,
			game["visitor"],
			game["visitor_score"],
			c_home,
			game["home"],
			game["home_score"],
			game["quarter"],
			game["time"]
		)
	
	def formatGameFuture(self, game):
		return "%s@%s" % (
			game["visitor"],
			game["home"]
		)
	
	def formatGamePast(self, game):
		c_vis = 3 if int(game["visitor_score"]) > int(game["home_score"]) else 4
		c_home = 4 if int(game["visitor_score"]) > int(game["home_score"]) else 3
		
		return "\x03%s%s(%s)\x03@\x03%s%s(%s)\x03" % (
			c_vis,
			game["visitor"],
			game["visitor_score"],
			c_home,
			game["home"],
			game["home_score"]
		)
	
	def getNflGamesCached(self):
		if time()-self.cacheAge > self.config["cache"]:
			self.cache = NFLLive.getNflGames()
			self.cacheAge = time()
		return self.cache
	
	@staticmethod
	def getNflGames():
		result = {}
		
		# Fetch NFL information as XML
		nflxml = get("http://www.nfl.com/liveupdate/scorestrip/ss.xml?random=1413140448433")
		doc = etree.fromstring(nflxml.content)
		games = doc.xpath("/ss/gms")[0]
		
		result["season"]={
			"week":games.attrib["w"],
			"year":games.attrib["y"],
			"type":NFLLive.translateSeasonType(games.attrib["t"]), # R for regular season, probably P for pre (?)
			"gameday":int(games.attrib["gd"]), # 1 or 0 for gameday or not (?)
			"bph":games.attrib["bph"] # not sure
		}
		result["games"]=[]
		
		for game in games.getchildren():
			gameblob = {
				"home":game.attrib["h"],
				"home_name":game.attrib["hnn"],
				"home_score":game.attrib["hs"],
				
				"visitor":game.attrib["v"],
				"visitor_name":game.attrib["vnn"],
				"visitor_score":game.attrib["vs"],
				
				"gametype":game.attrib["gt"], # REGular season, probably P for preseason (?)
				"quarter":game.attrib["q"], # P if not started, 1-4, F is finished
				"time":game.attrib["k"] if "k" in game.attrib else None,
				"id":game.attrib["eid"],
				"gamenum":game.attrib["gsis"],
				
				"starttime":game.attrib["t"],
				"startdate":datetime.strptime(game.attrib["eid"][0:-2]+" "+game.attrib["t"], "%Y%m%d %I:%M")+timedelta(hours=12) # NHL provides a 12 hour EST clock with all times PM. Add 12 hours so the datetime obj is PM instead of AM.
			}
			
			# Add 4 more hours to make it GMT
			gameblob["startdate_gmt"]=gameblob["startdate"]+timedelta(hours=4)
			gameblob["nfl_link"]="http://www.nfl.com/gamecenter/%s/%s/%s%s/%s@%s" % (
				gameblob["id"],
				result["season"]["year"],
				gameblob["gametype"],
				result["season"]["week"],
				gameblob["visitor_name"],
				gameblob["home_name"])
			
			result["games"].append(gameblob)
		return result
	
	@staticmethod
	def translateSeasonType(season):
		if season=="R":
			return "Regular"
		if season=="P":
			return "Pre"
		return season
