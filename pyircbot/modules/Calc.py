
from pyircbot.modulebase import ModuleBase, ModuleHook, MissingDependancyException, regex, command
from pyircbot.modules.ModInfo import info
import datetime
import time
import math


class Calc(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

        self.timers = {}

        self.sqlite = self.bot.getBestModuleForService("sqlite")
        if self.sqlite is None:
            raise MissingDependancyException("Calc: SQLIite service is required.")

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
        if channel not in self.timers:
            self.createDefaultTimers(channel)
        return time.time() - self.timers[channel][timetype]

    def updateTimeSince(self, channel, timetype):
        if channel not in self.timers:
            self.createDefaultTimers(channel)
        self.timers[channel][timetype] = time.time()

    def createDefaultTimers(self, channel):
        self.timers[channel] = {"add": 0, "calc": 0, "calcspec": 0, "match": 0}

    def remainingToStr(self, total, elasped):
        remaining = total - elasped
        minutes = int(math.floor(remaining / 60))
        seconds = int(remaining - (minutes * 60))
        return "Please wait %s minute(s) and %s second(s)." % (minutes, seconds)

    @info("quote [key[ =[ value]]]     set or update facts", cmds=["quote"])
    @regex(r'(?:^\.?(?:calc|quote)(?:\s+?(?:([^=]+)(?:\s?(=)\s?(.+)?)?)?)?)', types=['PRIVMSG'])
    def cmd_calc(self, message, match):
        word, changeit, value = match.groups()
        if word:
            word = word.strip()
        if value:
            value = value.strip()
        channel = message.args[0]
        sender = message.prefix.nick

        if word and changeit:
            # Add a new calc or delete
            if self.config["allowDelete"] and not value:
                result = self.deleteCalc(channel, word)
                if result:
                    self.bot.act_PRIVMSG(channel, "Calc deleted, %s." % sender)
                else:
                    self.bot.act_PRIVMSG(channel, "Sorry %s, I don't know what '%s' is." % (sender, word))
            else:
                if self.config["delaySubmit"] > 0 and self.timeSince(channel, "add") < self.config["delaySubmit"]:
                    self.bot.act_PRIVMSG(channel, self.remainingToStr(self.config["delaySubmit"],
                                                                      self.timeSince(channel, "add")))
                else:
                    self.addNewCalc(channel, word, value, sender, message.prefix.hostname)
                    self.bot.act_PRIVMSG(channel, "Thanks for the info, %s." % sender)
                    self.updateTimeSince(channel, "add")
        elif word:
            # Lookup the word in calc

            if self.config["delayCalcSpecific"] > 0 and \
               self.timeSince(channel, "calcspec") < self.config["delayCalcSpecific"]:
                self.bot.act_PRIVMSG(sender, self.remainingToStr(self.config["delayCalcSpecific"],
                                                                 self.timeSince(channel, "calcspec")))
            else:
                randCalc = self.getSpecificCalc(channel, word)
                if randCalc is None:
                    self.bot.act_PRIVMSG(channel, "Sorry %s, I don't know what '%s' is." % (sender, word))
                else:
                    self.bot.act_PRIVMSG(channel, "%s \x03= %s \x0314[added by: %s]" %
                                         (randCalc["word"], randCalc["definition"], randCalc["by"]))
                    self.updateTimeSince(channel, "calcspec")
        else:
            if self.config["delayCalc"] > 0 and self.timeSince(channel, "calc") < self.config["delayCalc"]:
                self.bot.act_PRIVMSG(sender, self.remainingToStr(self.config["delayCalc"],
                                                                 self.timeSince(channel, "calc")))
            else:
                randCalc = self.getRandomCalc(channel)
                if randCalc is None:
                    self.bot.act_PRIVMSG(channel, "This channel has no calcs, %s :(" % (sender,))
                else:
                    self.bot.act_PRIVMSG(channel, "%s \x03= %s \x0314[added by: %s]" % (randCalc["word"],
                                         randCalc["definition"], randCalc["by"]))
                    self.updateTimeSince(channel, "calc")

    @command("match", require_args=True)
    def cmd_match(self, msg, cmd):
        if self.config["delayMatch"] > 0 and self.timeSince(msg.args[0], "match") < self.config["delayMatch"]:
            self.bot.act_PRIVMSG(msg.prefix.nick, self.remainingToStr(self.config["delayMatch"],
                                                                      self.timeSince(msg.args[0], "match")))
        else:
            term = cmd.args_str
            if not term.strip():
                return
            c = self.sql.getCursor()
            channelId = self.getChannelId(msg.args[0])
            c.execute("SELECT * FROM `calc_words` WHERE `word` LIKE ? AND `channel`=? ORDER BY `word` ASC ;",
                      ("%%" + term + "%%", channelId))
            rows = c.fetchall()
            if not rows:
                self.bot.act_PRIVMSG(msg.args[0], "%s: Sorry, no matches" % msg.prefix.nick)
            else:
                matches = []
                for row in rows[0:10]:
                    if not row:
                        break
                    matches.append(row["word"])
                self.bot.act_PRIVMSG(msg.args[0], "%s: %s match%s (%s\x03)" %
                                     (msg.prefix.nick, len(matches), "es" if len(matches) > 1 else
                                                                     "", ", \x03".join(matches)))
                self.updateTimeSince(msg.args[0], "match")

    def addNewCalc(self, channel, word, definition, name, host):
        " Find the channel ID"
        channelId = self.getChannelId(channel)

        " Check if we need to add a user"
        c = self.sql.getCursor()
        c.execute("SELECT * FROM `calc_addedby` WHERE `username`=? AND `userhost`=? ;", (name, host))
        rows = c.fetchall()
        if not rows:
            c.execute("INSERT INTO `calc_addedby` (`username`, `userhost`) VALUES (?, ?) ;", (name, host,))
            c.execute("SELECT * FROM `calc_addedby` WHERE `username`=? AND `userhost`=? ;", (name, host))
            rows = c.fetchall()
        addedId = rows[0]["id"]

        " Check if the word exists"
        c.execute("SELECT * FROM `calc_words` WHERE `channel`=? AND `word`=? ;", (channelId, word))
        rows = c.fetchall()
        if not rows:
            c.execute("INSERT INTO `calc_words` (`channel`, `word`, `status`) VALUES (?, ?, ?) ;",
                      (channelId, word, 'approved'))
            c.execute("SELECT * FROM `calc_words` WHERE `channel`=? AND `word`=? ;", (channelId, word))
            rows = c.fetchall()
        wordId = rows[0]["id"]
        " Add definition "
        c.execute("INSERT INTO `calc_definitions` (`word`, `definition`, `addedby`, `date`, `status`) VALUES "
                  "(?, ?, ?, ?, ?) ;", (wordId, definition, addedId, datetime.datetime.now(), 'approved',))
        c.close()

    def getSpecificCalc(self, channel, word):
        c = self.sql.getCursor()
        channelId = self.getChannelId(channel)
        c.execute("SELECT `cw`.`word`, (SELECT `cdq`.`id` FROM `calc_definitions` `cdq` WHERE `cdq`.`word`=`cw`.`id` "
                  "AND `cdq`.`status`='approved' ORDER BY `cdq`.`date` DESC LIMIT 1) as `definitionId` FROM "
                  "`calc_words` `cw` WHERE `cw`.`channel`=? AND `cw`.`status`='approved' AND `cw`.`word`=? "
                  "COLLATE NOCASE ORDER BY RANDOM() LIMIT 1 ;", (channelId, word.lower()))
        word = c.fetchone()

        if word is None:
            return None

        c.execute("SELECT `ca`.`username`, `cd`.`definition` FROM `calc_definitions` `cd` JOIN `calc_addedby` `ca` ON "
                  "`ca`.`id` = `cd`.`addedby` WHERE `cd`.`id`=? LIMIT 1 ;", (word["definitionId"], ))

        who = c.fetchone()

        if who is None:
            return None

        c.close()
        return {"word": word["word"], "definition": who["definition"], "by": who["username"]}

    def getRandomCalc(self, channel):
        c = self.sql.getCursor()
        channelId = self.getChannelId(channel)

        for i in range(0, 5):
            c.execute("SELECT `cw`.`word`, (SELECT `cdq`.`id` FROM `calc_definitions` `cdq` WHERE "
                      "`cdq`.`word`=`cw`.`id` AND `cdq`.`status`='approved' ORDER BY `cdq`.`date` DESC LIMIT 1) as "
                      "`definitionId` FROM `calc_words` `cw` WHERE `cw`.`channel`=? AND `cw`.`status`='approved' "
                      "ORDER BY RANDOM() LIMIT 1 ;", (channelId,))
            word = c.fetchone()
            if word is None:
                return None
            c.execute("SELECT `ca`.`username`, `cd`.`definition` FROM `calc_definitions` `cd` JOIN `calc_addedby` `ca` "
                      "ON `ca`.`id` = `cd`.`addedby` WHERE `cd`.`id`=? LIMIT 1 ;", (word["definitionId"], ))

            who = c.fetchone()

            if who is None:
                continue

            c.close()
            return {"word": word["word"], "definition": who["definition"], "by": who["username"]}

    def deleteCalc(self, channel, word):
        " Return true if deleted something, false if it doesnt exist"
        c = self.sql.getCursor()
        channelId = self.getChannelId(channel)
        c.execute("SELECT * FROM `calc_words` WHERE `channel`=? and `word`=? ;", (channelId, word))
        rows = c.fetchall()
        if not rows:
            c.close()
            return False

        wordId = rows[0]["id"]

        # c.execute("DELETE FROM `calc_words` WHERE `id`=? ;", (wordId,))
        # c.execute("DELETE FROM `calc_definitions` WHERE `word`=? ;", (wordId,))
        c.execute("UPDATE `calc_definitions` SET `status`='deleted' WHERE `word`=? ;", (wordId,))

        c.close()
        return True

    def getChannelId(self, channel):
        c = self.sql.getCursor()
        c.execute("SELECT * FROM `calc_channels` WHERE `channel` = ?", (channel,))
        rows = c.fetchall()
        if not rows:
            c.execute("INSERT INTO `calc_channels` (`channel`) VALUES (?);", (channel,))
            c.execute("SELECT * FROM `calc_channels` WHERE `channel` = ?", (channel,))
            rows = c.fetchall()
        chId = rows[0]["id"]
        c.close()
        return chId
