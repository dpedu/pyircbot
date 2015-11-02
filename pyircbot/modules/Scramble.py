"""
.. module:: Scramble
    :synopsis: Module to provide a word scramble game

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
import random
import json
import os
import time
from threading import Timer
from operator import itemgetter

class Scramble(ModuleBase):
    def __init__(self, bot, moduleName):
        # init the base module
        ModuleBase.__init__(self, bot, moduleName);
        self.hooks=[ModuleHook("PRIVMSG", self.scramble)]
        self.loadConfig()
        
        # Dictionary
        self.wordsCount=0;
        self.wordsFile = self.getFilePath("words.txt")
        print(self.wordsFile)
        wordsF = open(self.wordsFile, "r")
        while True:
            word = wordsF.readline()
            if word=="":
                break
            self.wordsCount+=1
        wordsF.close
        self.log.info("Scramble: Loaded %s words" % str(self.wordsCount))
        # Load scores
        self.scoresFile = self.getFilePath("scores.json")
        if not os.path.exists(self.scoresFile): 
            json.dump({}, open(self.scoresFile, 'w'))
        self.scores = json.load(open(self.scoresFile, 'r'))
        # Per channel games
        self.games = {}
        # Hook in
        self.hooks=[ModuleHook("PRIVMSG", self.scramble)]
    
    def scramble(self, args, prefix, trailing):
        channel = args[0]
        if channel[0] == "#":
            if not channel in self.games:
                self.games[channel]=scrambleGame(self, channel)
            self.games[channel].scramble(args, prefix, trailing)
    
    def saveScores(self):
        json.dump(self.scores, open(self.scoresFile, 'w'))
    
    def getScore(self, player, add=0):
        player = player.lower()
        if not player in self.scores:
            self.scores[player] = 0
        if not add == 0:
            self.scores[player]+=add
            self.saveScores()
            
        return self.scores[player]
    
    def getScoreNoWrite(self, player):
        if not player.lower() in self.scores:
            return 0
        else:
            return self.getScore(player)
    
    def ondisable(self):
        self.log.info("Scramble: Unload requested, ending games...")
        for game in self.games:
            self.games[game].gameover()
        self.saveScores()

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
        # How many gamesWithoutGuesses submitted this round
        self.guesses = 0;
        # How many games in a row where nobody guessed
        self.gamesWithoutGuesses = 0;
        
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
        cmd = self.master.bot.messageHasCommand(".scrambleon", trailing)
        if cmd and not self.running:
            self.running = True
            self.startScramble()
            return
        cmd = self.master.bot.messageHasCommand(".scrambleoff", trailing)
        if cmd and self.running:
            self.gameover()
            self.running = False
            return
        cmd = self.master.bot.messageHasCommand(".scramble top", trailing)
        if cmd:
            sortedscores = []
            for player in self.master.scores:
                sortedscores.append({'name':player, 'score':self.master.scores[player]})
            sortedscores = sorted(sortedscores, key=itemgetter('score'))
            sortedscores.reverse()
            numScores = len(sortedscores)
            if numScores>3:
                numScores=3
            resp = "Top %s: " % str(numScores)
            which = 1
            while which<=numScores:
                resp+="%s: %s, " % (sortedscores[which-1]["name"], sortedscores[which-1]["score"])
                which+=1
            self.master.bot.act_PRIVMSG(self.channel, resp[:-2])
        cmd = self.master.bot.messageHasCommand(".scramble score", trailing)
        if cmd:
            someone = cmd.args.strip()
            if len(someone) > 0:
                self.master.bot.act_PRIVMSG(self.channel, "%s: %s has a score of %s" % (sender, someone, self.master.getScoreNoWrite(someone)))
            else: 
                self.master.bot.act_PRIVMSG(self.channel, "%s: %s" % (sender, self.master.getScore(sender)))
        if self.currentWord and trailing.strip().lower() == self.currentWord:
            playerScore = self.master.getScore(sender, 1)
            self.master.bot.act_PRIVMSG(self.channel, "%s guessed the word - %s! %s now has %s points. Next word in %s seconds." % (sender, self.currentWord, sender, playerScore, self.delayNext))
            self.currentWord = None
            self.clearTimers()
            self.hintsGiven = 0
            self.nextTimer = Timer(self.delayNext, self.startNewWord)
            self.nextTimer.start()
            self.guesses=0
        else:
            self.guesses+=1
            
    def startScramble(self):
        self.clearTimer(self.nextTimer)
        self.nextTimer = Timer(0, self.startNewWord)
        self.nextTimer.start()
        
    def startNewWord(self):
        self.currentWord = self.pickWord()
        self.master.log.info("Scramble: New word for %s: %s" % (self.channel, self.currentWord))
        self.scrambled = self.scrambleWord(self.currentWord)
        self.master.bot.act_PRIVMSG(self.channel, "New word - %s " % (self.scrambled))
        
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
        self.master.bot.act_PRIVMSG(self.channel, "Word expired - the answer was %s. Next word in %s seconds." % (cur, self.delayNext))
        self.hintsGiven = 0
        self.clearTimer(self.nextTimer)
        
        if self.guesses==0:
            self.gamesWithoutGuesses+=1
            if self.gamesWithoutGuesses >= self.abortAfterNoGuesses:
                self.master.bot.act_PRIVMSG(self.channel, "No one seems to be playing - type .scrambleon to start again.")
                self.gameover()
                return
        else:
            self.gamesWithoutGuesses=0
                
        self.nextTimer = Timer(self.delayNext, self.startNewWord)
        self.nextTimer.start()
        
    def pickWord(self):
        f = open(self.master.wordsFile, "r")
        skip = random.randint(0, self.master.wordsCount)
        while skip>=0:
            f.readline()
            skip-=1
        picked = f.readline().strip().lower()
        f.close()
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