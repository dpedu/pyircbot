#!/usr/bin/env python
"""
.. module::CardsAgainstHumanity
    :synopsis: Cards against Humanity, in IRC. Cards against IRC?
.. moduleauthor:: Nick Krichevsky <nick@ollien.com>

"""
from pyircbot.modulebase import ModuleBase,ModuleHook
import os
import time
from threading import Timer
from operator import itemgetter
from random import choice

class CardsAgainstHumanity(ModuleBase):
    def __init__(self, bot, moduleName):
        # init the base module
        ModuleBase.__init__(self, bot, moduleName);
        self.hooks=[ModuleHook("PRIVMSG", self.scramble)]
        
        # Dictionary
        self.whitesFile = open(self.getFilePath("answers.txt"),'r')
        self.blacksFile = open(self.getFilePath("questions.txt"),'r')
        self.whites = [line.rstrip() for line in self.whitesFile]
        self.blacks = [line.rstrip() for line in self.blacksFile]
        self.currentBlack = ""
        self.whitesFile.close()
        self.blacksFile.close()
        self.log.info("CAH: Loaded."+str(len(self.whites))+" White Cards "+str(len(self.blacks))+" Black Cards")
        # Per channel games
        self.games = {}
        
    
    def scramble(self, args, prefix, trailing):
        channel = args[0]
        if channel[0] == "#":
            if not channel in self.games:
                self.games[channel]=cardsGame(self, channel,self.whites,self.blacks)
            self.games[channel].stuff(args, prefix, trailing)
    
    
    def ondisable(self):
        self.log.info("CAH: Unload requested, ending games...")
        # for game in self.games:
        #     self.games[game].gameover()

class cardsGame:
    def __init__(self, master, channel,whites,blacks):
        self.master = master
        self.channel = channel
        # Running?
        self.running = False
        # Current word
        # self.message = 'xmopxshell has downs'
        self.players = {}
        self.timers = {}
        self.whites = whites
        self.blacks = blacks
        self.lastCzar = -1
        self.czar = ""
        self.started = False
        self.active = False
        self.allowPick = 0
        self.choices = {}
        self.czarTimer = None
    def stuff(self, args, prefix, trailing):
        prefix = self.master.bot.decodePrefix(prefix)
        sender = prefix.nick
        if self.master.bot.messageHasCommand(".joinGame", trailing):
            self.join(sender)
        elif self.master.bot.messageHasCommand(".ready",trailing):
            result = self.markReady(sender)
            if result:
                self.started = True
                self.master.bot.act_PRIVMSG(self.channel,"All players are ready!")
                for player in self.players:
                    self.master.bot.act_PRIVMSG(player,"ITS TIME TO D-D-D-D-D-DUEL!")    
                    self.players[player]=[]
                for player in self.players:
                    self.deal(player)
                    self.sendCards(player)
                self.active = True
                self.makeTurn()
        elif self.master.bot.messageHasCommand(".pick",trailing):
            if self.active:
                if sender != self.czar:
                    print(sender,self.czar)
                    print(sender !=  self.czar)
                    if self.allowPick > 0:
                        if sender in self.players:
                            cards = trailing.split(' ')[1:]
                            if len(cards)==self.allowPick:
                                if self.checkBounds(cards):
                                    if sender not in self.choices:
                                        cardChoices = [self.players[sender][int(index)] for index in cards]
                                        print(cardChoices)
                                        self.choices[sender] = cardChoices
                                        self.removeAndReplenishCards(sender, cardChoices)
                                        self.sendCards(sender)
                                        del self.choices[sender]
                                        if sender in timers:
                                            self.timers[sender].cancel()
                                    if self.allDrawn():
                                        self.readChoices()
                                        self.master.bot.act_PRIVMSG(self.channel,self.czar+"! Please choose the winner!")
                                        czarTimer = Timer(180,self.kick,(self.czar,"taking too long to pick a choice. The next turn iwll be made."))
                                        self.makeTurn()
                                    
                                else:
                                    self.master.bot.act_PRIVMSG(self.channel,sender+", you picked a card that was out of the range. Please don't do that.")
                            else:
                                self.master.bot.act_PRIVMSG(self.channel,sender+", you picked "+str(len(cards))+" cards. You were supposed to pick "+str(self.allowPick))
        elif self.master.bot.messageHasCommand(".choose",trailing):
            if sender==self.czar:
                choice = trailing.split()[1:]
                if len(choice)==1:
                    if self.checkChoiceBounds(int(choice[0])):
                        self.master.bot.act_PRIVMSG(self.channel,list(self.choices.keys())[int(choice[0])]+", you won the round!")
                        if self.czarTimer!=None:
                            self.czarTimer.cancel()
                        self.makeTurn()
                    else:
                        self.master.bot.act_PRIVMSG(self.channel,sender+", your choice was out of the range. Please don't do that.")
                else:
                    self.master.bot.act_PRIVMSG(self.channel,sender+", you picked "+str(len(choice))+" "+" winners. You were only supposed to pick 1.")
        elif self.master.bot.messageHasCommand('.leave',trailing):
            if sender in self.players:
                self.kick(sender,'choosing to leave the game you dolt')
                if sender is self.czar:
                    self.makeTurn()
                    
    def join(self,nick):
        if not self.started:
            if nick not in self.players:
                self.players[nick]=False
                self.master.bot.act_PRIVMSG(self.channel, nick+" has joined the game! | The players currently are "+str(self.players))
        else:
            print("the game has already started!")
            self.master.bot.act_PRIVMSG(self.channel,"The game has already started!")
    def markReady(self,nick):
        if not self.started:
            if nick in self.players:
                self.players[nick]=True
                for player in self.players:
                    print(player)
                    if not self.players[player]:
                        print (player+" not ready")
                        return False
                return True
            else:
                self.master.bot.act_PRIVMSG(self.channel, "You are not in the game! Type .joinGame!")
        else:
            print("game has already started!")
            self.master.bot.act_PRIVMSG(self.channel,"The game has already started!")
    def deal(self,nick):
        self.players[nick] = [self.pickWhite() for i in range (7)]
    def pickWhite(self):
        card = choice(self.whites)
        self.whites.remove(card)
        return card
    def pickBlack(self):
        card = choice(self.blacks)
        self.blacks.remove(card)
        return card
    def sendCards(self,nick):
        cards = ""
        for card in self.players[nick]:
            cards+=str(self.players[nick].index(card))+". "
            cards+=card+" "
        self.master.bot.act_PRIVMSG(nick,"Your cards are "+cards)
    def readCard(self,card):
        count = card.count('_')
        if count == 0:
            if 'haiku' in card:
                count = 3
            else:
                count = 1
        self.master.bot.act_PRIVMSG(self.channel,"The black card is \""+card+"\" Pick "+str(count))
        return count
    def pickCzar(self):
        index = self.lastCzar+1
        if index < len(self.players):
            self.lastCzar = index
            return index
        else:
            self.lastCzar = 0
            return 0
    def announceCzar(self):
        self.master.bot.act_PRIVMSG(self.channel,"The Czar is "+self.czar+"!")
    def checkBounds(self,cards):
        for item in cards:
            if int(item)>6 or int(item)<0:
                return False
        return True
    def checkChoiceBounds(self,choice):
        if choice<0 or choice>len(self.choices)-1:
            return False
        return True
    def makeTurn(self):
        self.choices.clear()
        card = self.pickBlack()
        self.timers.clear()
        self.currentBlack = card
        self.allowPick = self.readCard(card)
        self.lastCzar = self.pickCzar()
        self.czar = list(self.players.keys())[self.lastCzar]
        print (self.lastCzar,self.czar)
        for player in self.players:
            if player!=self.czar:
                self.timers[player] = Timer(180,self.kick,(player,"taking more than 180 seconds for their turn."))
                self.timers[player].start()
        self.announceCzar()
    def kick(self,nick,reason):
        del self.players[nick]
        if nick in self.timers:
            self.timers[nick].cancel()
            del self.timers[nick]
        self.master.bot.act_PRIVMSG(self.channel,nick+" has been kicked due to "+reason)
        if len(self.players)<=1:
            self.master.bot.act_PRIVMSG(self.channel,"The game is being shut down due to having <=1 players")
            self.started = False
            self.active = False
            for timer in self.timers:
                timer.cancel()
            self.timers.clear()
            self.players.clear()
    def removeAndReplenishCards(self,nick,cards):
        for card in cards:
            self.players[nick].remove(card)
            self.players[nick].append(self.pickWhite())
    def readChoices(self):
        if '_' in self.currentBlack:
            for player in list(self.choices.keys()):
                cardInstance = str(list(self.choices.keys()).index(player))+". "+self.currentBlack
                cardInstance = list(cardInstance) #do this as opposed to space to preserve spaces
                for choice in self.choices[player]:
                    for char in cardInstance:
                        if char=='_':
                            print(char)
                            choice = choice.replace('.','')
                            cardInstance[cardInstance.index(char)] = choice
                            break
                self.master.bot.act_PRIVMSG(self.channel,''.join(cardInstance))
        else:
            for player in self.choices:
                self.master.bot.act_PRIVMSG(self.channel,self.currentBlack+' '+' '.join(self.choices[player]))
                    
    def allDrawn(self):
        for player in self.players:
            if player not in self.choices:
                if player != self.czar:
                    return False
        return True

