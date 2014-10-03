#!/usr/bin/env python
"""
.. module:: DogeDice
	:synopsis: Module to provide a game for gambling Dogecoin

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from modulebase import ModuleBase,ModuleHook
import random
import yaml
import os
import time
import math
import hashlib
from threading import Timer

class DogeDice(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.gotMsg)]
		self.loadConfig()
		# Load attribute storage
		self.attr = self.bot.getBestModuleForService("attributes")
		# Load doge RPC
		self.doge = self.bot.getBestModuleForService("dogerpc")
		# Dict of #channel -> game object
		self.games = {}
	
	def gotMsg(self, args, prefix, trailing):
		prefixObj = self.bot.decodePrefix(prefix)
		# Ignore messages from users not logged in
		loggedinfrom = self.attr.getKey(prefixObj.nick, "loggedinfrom")
		if loggedinfrom==None:
			# Send them a hint?
			return
		elif prefixObj.hostname == loggedinfrom:
			if args[0][0] == "#":
				# create a blank game obj if there isn't one (and whitelisted ? )
				if not args[0] in self.games and (not self.config["channelWhitelistOn"] or (self.config["channelWhitelistOn"] and args[0][1:] in self.config["channelWhitelist"]) ):
					self.games[args[0]]=gameObj(self, args[0])
				# Channel message
				self.games[args[0]].gotMsg(args, prefix, trailing)
			else:
				# Private message
				#self.games[args[0].gotPrivMsg(args, prefix, trailing)
				pass
		else:
			# Ignore potential spoofing
			pass
	
	def removeGame(self, channel):
		del self.games[channel]
	
	def ondisable(self):
		self.log.info("DogeDice: Unload requested, ending games...")
		while len(self.games)>0:
			first = list(self.games.keys())[0]
			self.games[first].gameover()

class gameObj:
	def __init__(self, master, channel):
		self.master = master
		self.channel = channel
		# Game state
		# 0 = waiting for players
		#     - advertise self?
		#     - players must be registered and have enough doge for current bet
		# 1 = enough players, countdown
		#     - Last warning to pull out
		# 2 = locked in / game setup
		#     - Move doge from player's wallets to table wallet. kick players if they can't afford
		# 3 = start of a round
		#     - Each player's turn to roll
		# 4 = determine winner, move doge
		#     - if > 10 doge, house fee?
		self.step = 0
		
		# Bet amount
		self.bet = 0.0
		# players list
		self.players = []
		# min players
		self.minPlayers = 2
		# max players
		self.maxPlayers = 4
		# Lobby countdown timer
		self.startCountdownTimer = None
		# pre-result timer
		self.endgameResultTimer = None
		# in-game timeout 
		self.playTimeout = None
		# Wallet for this game
		self.walletName = None
	
	def getPlayer(self, nick):
		for player in self.players:
			if player.nick == nick:
				return player
		return None
	
	def gotPrivMsg(self, args, prefix, trailing):
		prefix = self.master.bot.decodePrefix(prefix)
		pass
	
	def gotMsg(self, args, prefix, trailing):
		prefix = self.master.bot.decodePrefix(prefix)
		if self.step == 0 or self.step == 1:
			# Join game
			cmd = self.master.bot.messageHasCommand(".join", trailing)
			if cmd:
				if len(self.players)-1 < self.maxPlayers:
					if self.getPlayer(prefix.nick)==None:
						userWallet = self.master.attr.getKey(prefix.nick, "dogeaccountname")
						if userWallet == None:
							self.master.bot.act_PRIVMSG(self.channel, "%s: You don't have enough DOGE!" % (prefix.nick))
							return
						balance = self.master.doge.getBal(userWallet)
						
						# check if the room is 'opened' already:
						if len(self.players)==0:
							# require an amount
							if len(cmd.args)==1:
								# Check if they have enough coins
								try:
									bet = float(cmd.args[0])
								except:
									return
								
								if bet < self.master.config["minBet"]:
									self.master.bot.act_PRIVMSG(self.channel, "%s: Minimum bet is %s DOGE!" % (prefix.nick, self.master.config["minBet"]))
									return
								
								if balance>=bet:
									newPlayer = playerObj(self, prefix.nick)
									newPlayer.dogeWalletName = userWallet
									self.players.append(newPlayer)
									self.bet = bet
									self.master.bot.act_PRIVMSG(self.channel, "%s: You have joined!" % (prefix.nick))
								else:
									self.master.bot.act_PRIVMSG(self.channel, "%s: You don't have enough DOGE!" % (prefix.nick))
							else:
								self.master.bot.act_PRIVMSG(self.channel, "%s: You need to specify a bet amount: .join 10" % (prefix.nick))
						else:
							# no amount required
							if balance>=self.bet:
								newPlayer = playerObj(self, prefix.nick)
								newPlayer.dogeWalletName = userWallet
								self.players.append(newPlayer)
								self.master.bot.act_PRIVMSG(self.channel, "%s: You have joined!" % (prefix.nick))
								if self.canStart() and self.startCountdownTimer == None:
									self.initStartCountdown()
									self.master.bot.act_PRIVMSG(self.channel, "The game will start in %s seconds! Bet is %s DOGE each!" % (self.master.config["lobbyIdleSeconds"], self.bet))
							else:
								self.master.bot.act_PRIVMSG(self.channel, "%s: You don't have enough DOGE!" % (prefix.nick))
						
					else:
						self.master.bot.act_PRIVMSG(self.channel, "%s: you're already in the game. Quit with .leave" % (prefix.nick))
				else:
					self.master.bot.act_PRIVMSG(self.channel, "%s: the game is full (%s/%)! Cannot join." % (prefix.nick, len(self.players), self.maxPlayers))
			# Leave game
			cmd = self.master.bot.messageHasCommand(".leave", trailing)
			if cmd:
				if self.getPlayer(prefix.nick)==None:
					self.master.bot.act_PRIVMSG(self.channel, "%s: You're not in the game." % (prefix.nick))
				else:
					self.removePlayer(prefix.nick)
					self.master.bot.act_PRIVMSG(self.channel, "%s: You have left the game!" % (prefix.nick))
					if not self.canStart() and self.startCountdownTimer:
						self.clearTimer(self.startCountdownTimer)
						self.startCountdownTimer = None
						self.master.bot.act_PRIVMSG(self.channel, "Game start aborted." )
						self.step = 0
		elif self.step == 2:
			pass
		elif self.step == 3:
			# Ignore cmds from people outside the game
			player = self.getPlayer(prefix.nick)
			if not player:
				return
			
			# handle a .roll
			cmd = self.master.bot.messageHasCommand(".roll", trailing)
			if cmd and not player.hasRolled:
				roll1 = random.randint(1,6)
				roll2 = random.randint(1,6)
				self.master.bot.act_PRIVMSG(self.channel, "%s rolls %s and %s!" % (prefix.nick, roll1, roll2))
				player.hasRolled = True
				player.rollValue = roll1+roll2
			
			# Check if all players have rolled
			for player in self.players:
				if not player.hasRolled:
					return
			
			# start endgame timer
			self.step = 4
			self.endgameResultTimer = Timer(2, self.endgameResults)
			self.endgameResultTimer.start()
			
		elif self.step == 4:
			pass
		
		#senderIsOp = self.master.attr.getKey(prefix.nick, "op")=="yes"
	def clearTimer(self, timer):
		if timer:
			timer.cancel()
		timer = None
	
	def removePlayer(self, playerNick):
		pos = -1
		for i in range(0, len(self.players)):
			if self.players[i].nick == playerNick:
				pos = i
				break
		if pos >= 0:
			self.players.pop(pos)
	
	def canStart(self):
		# Return true if the step is 'lobby' mode and player count is OK
		return self.step == 0 and len(self.players)>=self.minPlayers
	def initStartCountdown(self):
		# Start the game-start countdown
		self.startCountdownTimer = Timer(self.master.config["lobbyIdleSeconds"], self.lobbyCountdownDone)
		self.startCountdownTimer.start()
		self.step = 1
	
	def lobbyCountdownDone(self):
		self.step = 2
		self.master.bot.act_PRIVMSG(self.channel, "Collecting DOGE and starting game.. Type .roll !")
		# Make a wallet for this game
		self.walletName = "DogeDice-"+self.channel
		# Generate an address to 'create' a wallet
		self.master.doge.getAcctAddr(self.walletName)
		
		# Verify and move funds from each player
		for player in self.players:
			playerBalance = self.master.doge.getAcctBal(player.dogeWalletName)
			if playerBalance < self.bet:
				self.master.bot.act_PRIVMSG(self.channel, "%s was dropped from the game!")
				self.removePlayer(player.nick)
		
		if len(self.players) <= 1:
			self.master.bot.act_PRIVMSG(self.channel, "1 or players left - game over!")
			self.resetGame()
			return
		
		# Take doges
		for player in self.players:
			self.master.doge.move(player.dogeWalletName, self.walletName, self.bet)
		
		# Pre-game setup (nothing !)
		
		# Accept game commands
		self.step = 3
		
		# Start play timeout
		self.playTimeout = Timer(30, self.gamePlayTimeoutExpired)
		self.playTimeout.start()
	
	def gamePlayTimeoutExpired(self):
		# Time out - return doges
		self.master.bot.act_PRIVMSG(self.channel, "Time expired! Returning all doges.")
		if self.step == 3:
			# In game step. Refund doges
			for player in self.players:
				self.master.doge.move(self.walletName, player.dogeWalletName, self.bet)
		self.resetGame()
	
	def endgameResults(self):
		maxRollNames = []
		maxRollValue = 0
		for player in self.players:
			if player.rollValue > maxRollValue:
				maxRollNames = []
				maxRollNames.append(player.nick)
				maxRollValue = player.rollValue
			if player.rollValue == maxRollValue:
				if not player.nick in maxRollNames:
					maxRollNames.append(player.nick)
		
		pot = self.master.doge.getAcctBal(self.walletName)
		DOGEeachDec = pot/len(maxRollNames)
		DOGEeach = math.floor(DOGEeachDec*100000000) / 100000000
		
		if len(maxRollNames)==1:
			self.master.bot.act_PRIVMSG(self.channel, "We have a winner - %s! Winnings are: %s DOGE" % (maxRollNames[0], DOGEeach))
		else:
			self.master.bot.act_PRIVMSG(self.channel, "We have a tie between %s - The take is %s DOGE each" % (' and '.join(maxRollNames), DOGEeach))
		
		# Pay out
		for nick in maxRollNames:
			player = self.getPlayer(nick)
			self.master.doge.move(self.walletName, player.dogeWalletName, DOGEeach)
		
		# the end!
		self.resetGame()
	
	def resetGame(self):
		self.clearTimer(self.startCountdownTimer)
		self.startCountdownTimer = None
		self.clearTimer(self.endgameResultTimer)
		self.endgameResultTimer = None
		self.clearTimer(self.playTimeout)
		self.playTimeout = None
		self.master.removeGame(self.channel)
	
	def gameover(self):
		self.gamePlayTimeoutExpired()
	

class playerObj:
	def __init__(self, game, nick):
		self.game = game
		self.nick = nick
		# Save the player's wallet name
		self.dogeWalletName = None
		# Set to true after they roll
		self.hasRolled = False
		# Sum of their dice
		self.rollValue = None
	
