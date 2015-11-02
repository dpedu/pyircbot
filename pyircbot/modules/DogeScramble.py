#!/usr/bin/env python
"""
.. module:: DogeScramble
    :synopsis: This module provides a word scrambling game that rewards winners with small amounts of Dogecoin

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
import random
import os
import time
from threading import Timer

class DogeScramble(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName);
        self.hooks=[ModuleHook("PRIVMSG", self.scramble)]
        self.loadConfig()
        
        # Load attribute storage
        self.attr = None
        serviceProviders = self.bot.getmodulesbyservice("attributes")
        if len(serviceProviders)==0:
            self.log.error("DogeScramble: Could not find a valid attributes service provider")
        else:
            self.log.info("DogeScramble: Selecting attributes service provider: %s" % serviceProviders[0])
            self.attr = serviceProviders[0]
        
        # Load doge RPC
        self.doge = self.bot.getBestModuleForService("dogerpc")
        
        # Per channel games
        self.games = {}
    
    def scramble(self, args, prefix, trailing):
        channel = args[0]
        if channel[0] == "#":
            # Ignore messages from users without a dogewallet password
            prefixObj = self.bot.decodePrefix(prefix)
            if self.attr.getKey(prefixObj.nick, "password")==None:
                return
            if not channel in self.games:
                self.games[channel]=scrambleGame(self, channel)
            self.games[channel].scramble(args, prefix, trailing)
    def ondisable(self):
        self.log.info("DogeScramble: Unload requested, ending games...")
        for game in self.games:
            self.games[game].gameover()

class scrambleGame:
    def __init__(self, master, channel):
        self.master = master
        self.channel = channel
        # Running?
        self.running = False
        # Current word
        self.currentWord = None
        # Current word, scrambled
        self.scrambled = None
        # Online?
        self.scrambleOn = False
        # Count down to hints
        self.hintTimer = None
        # of hints given
        self.hintsGiven = 0
        # Cooldown between words
        self.nextTimer = None
        # How many guesses submitted this round
        self.guesses = 0;
        # How many games in a row where nobody guessed
        self.gamesWithoutGuesses = 0;
        # What file are we using
        self.category_file = None;
        # How many words in this category have been used? 
        self.category_count = 0
        # How long between categories
        self.change_category_after_words = self.master.config["categoryduration"]
        # Should we change categories at the next pick?
        self.should_change_category = True
        # Holds the processed category name
        self.category_name = None
        # list of last picked words
        self.lastwords = []
        # name of last winner for decreasing return
        self.lastwinner = None
        self.lastwinvalue = 0
        
        self.delayHint = self.master.config["hintDelay"];
        self.delayNext = self.master.config["delayNext"];
        self.maxHints = self.master.config["maxHints"];
        self.abortAfterNoGuesses = self.master.config["abortAfterNoGuesses"];
        
    def gameover(self):
        self.clearTimers();
        self.running = False
    def clearTimers(self):
        self.clearTimer(self.nextTimer)
        self.clearTimer(self.hintTimer)
    def clearTimer(self, timer):
        if timer:
            timer.cancel()
    def scramble(self, args, prefix, trailing):
        prefix = self.master.bot.decodePrefix(prefix)
        sender = prefix.nick
        
        senderIsOp = self.master.attr.getKey(prefix.nick, "op")=="yes"
        
        cmd = self.master.bot.messageHasCommand(".scramble", trailing)
        if cmd and not self.running:
            #and senderIsOp 
            self.running = True
            self.startScramble()
            return
        cmd = self.master.bot.messageHasCommand(".scrambleoff", trailing)
        if cmd and senderIsOp and self.running:
            self.gameover()
            self.running = False
            return
        
        if self.currentWord and trailing.strip().lower() == self.currentWord:
            # Get winner withdraw address
            useraddr = self.master.attr.getKey(prefix.nick, "dogeaddr")
            userwallet = self.master.attr.getKey(prefix.nick, "dogeaccountname")
            
            self.master.bot.act_PRIVMSG(self.channel, "%s got the word - %s!" % (sender, self.currentWord))
            
            if not useraddr:
                self.master.bot.act_PRIVMSG(self.channel, "%s: to win DOGE, you must set an wallet address by PMing me \".setdogeaddr\". Next word in %s seconds." % (prefix.nick, self.delayNext))
            else:
                winamount = float(self.master.config["winAmount"])
                if self.lastwinner == prefix.nick:
                    winamount = self.lastwinvalue * self.master.config["decreaseFactor"]
                self.lastwinvalue = winamount
                self.lastwinner = prefix.nick
                
                self.master.bot.act_PRIVMSG(self.channel, "%s won %s DOGE! Next word in %s seconds." % (prefix.nick, round(winamount, 8), self.delayNext))
                self.master.doge.move('', userwallet, winamount)
            
            self.currentWord = None
            self.clearTimers()
            self.hintsGiven = 0
            self.nextTimer = Timer(self.delayNext, self.startNewWord)
            self.nextTimer.start()
            self.guesses=0
            self.category_count+=1
            self.master.log.debug("DogeScramble: category_count is: %s" % (self.category_count))
            if self.category_count >= self.change_category_after_words:
                self.should_change_category = True
        else:
            self.guesses+=1
            
    def startScramble(self):
        self.clearTimer(self.nextTimer)
        self.nextTimer = Timer(0, self.startNewWord)
        self.nextTimer.start()
        
    def startNewWord(self):
        self.currentWord = self.pickWord()
        self.scrambled = self.scrambleWord(self.currentWord)
        self.master.bot.act_PRIVMSG(self.channel, "[Category: %s] Unscramble this: %s " % (self.category_name, self.scrambled))
        
        self.clearTimer(self.hintTimer)
        self.hintTimer = Timer(self.delayHint, self.giveHint)
        self.hintTimer.start()
        
    def giveHint(self):
        self.hintsGiven+=1
        
        if self.hintsGiven>=len(self.currentWord) or self.hintsGiven > self.maxHints:
            self.abortWord()
            return
        
        blanks = ""
        for letter in list(self.currentWord):
            if letter == " ":
                blanks+=" "
            else:
                blanks+="_"
        partFromWord = self.currentWord[0:self.hintsGiven]
        partFromBlanks = blanks[self.hintsGiven:]
        hintstr = partFromWord+partFromBlanks
        
        self.master.bot.act_PRIVMSG(self.channel, "Hint: - %s" % (hintstr))
        
        self.clearTimer(self.hintTimer)
        self.hintTimer = Timer(self.delayHint, self.giveHint)
        self.hintTimer.start()
    
    def abortWord(self):
        cur = self.currentWord
        self.currentWord = None
        self.master.bot.act_PRIVMSG(self.channel, "Word expired - the answer was '%s'. Next word in %s seconds." % (cur, self.delayNext))
        self.hintsGiven = 0
        self.clearTimer(self.nextTimer)
        
        if self.guesses==0:
            self.gamesWithoutGuesses+=1
            if self.gamesWithoutGuesses >= self.abortAfterNoGuesses:
                self.master.bot.act_PRIVMSG(self.channel, "No one seems to be playing - type .scramble to start again.")
                self.gameover()
                return
        else:
            self.gamesWithoutGuesses=0
                
        self.nextTimer = Timer(self.delayNext, self.startNewWord)
        self.nextTimer.start()
    
    def catFileNameToStr(self, s):
        s=s.split(".")[0]
        s=s.replace("_", " ")
        return s.title()
    
    def pickWord(self):
        if self.should_change_category:
            # clear flags
            self.should_change_category = False
            self.category_count = 0
            # Get the path to word files dir
            dirpath = self.master.getFilePath("")
            # List dir
            files = os.listdir(dirpath)
            # choose a random file
            random.shuffle(files)
            self.category_file = files[0]
            self.category_name = self.catFileNameToStr(self.category_file)
            # Process the name & announce
            self.master.bot.act_PRIVMSG(self.channel, "The category is now: %s " % self.category_name)
        # count lines
        f = open(self.master.getFilePath(self.category_file), "r")
        lines = 0
        while True:
            lines+=1
            if f.readline() == "":
                break
        f.close()
        # change category
        picked = ""
        while picked == "" or picked in self.lastwords:
            
            skip = random.randint(0, lines)
            f = open(self.master.getFilePath(self.category_file), "r")
            while skip>=0:
                f.readline()
                skip-=1
            picked = f.readline().strip().lower()
            f.close()
        
        self.master.log.debug("DogeScramble: picked %s for %s" % (picked, self.channel))
        self.lastwords.append(picked)
        if len(self.lastwords) > 5:
            self.lastwords.pop(0)
        return picked
        
    def scrambleWord(self, word):
        scrambled = ""
        for subword in word.split(" "):
            scrambled+=self.scrambleIndividualWord(subword)+ " "
        return scrambled.strip()
        
    def scrambleIndividualWord(self, word):
        scrambled = list(word)
        random.shuffle(scrambled)
        return ''.join(scrambled).lower()
