"""
.. module:: Remind
    :synopsis: A module to support reminders

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
from datetime import datetime,timedelta
from threading import Thread
from time import sleep
import re
import pytz

class Remind(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName);
        
        self.db = None
        serviceProviders = self.bot.getmodulesbyservice("sqlite")
        if len(serviceProviders)==0:
            self.log.error("Remind: Could not find a valid sqlite service provider")
        else:
            self.log.info("Remind: Selecting sqlite service provider: %s" % serviceProviders[0])
            self.db = serviceProviders[0].opendb("remind.db")
        
        if not self.db.tableExists("reminders"):
            self.log.info("Remind: Creating table: reminders")
            c = self.db.query("""CREATE TABLE IF NOT EXISTS `reminders` (
            `id` INTEGER PRIMARY KEY,
            `sender` varchar(64),
            `senderch` varchar(64),
            `when` timestamp,
            `message` varchar(2048)
            ) ;""")
            c.close()
        
        self.hooks=[ModuleHook("PRIVMSG", self.remindin),ModuleHook("PRIVMSG", self.remindat)]
        
        self.disabled = False
        
        # Start monitor thread
        self.t = Thread(target=self.monitor_thread)
        self.t.daemon=True
        self.t.start()
        
    
    def monitor_thread(self):
        while True:
            sleep(self.config["precision"])
            if self.disabled:
                break
            self.monitor()
    
    def monitor(self):
        remindPeople = self.db.query("SELECT * FROM `reminders` WHERE `when` < ?", (datetime.now(),))
        reminders = remindPeople.fetchall()
        remindPeople.close()
        
        byrecip = {}
        
        for reminder in reminders:
            if not reminder["sender"] in byrecip:
                byrecip[reminder["sender"]]=[]
            
            byrecip[reminder["sender"]].append(reminder)
        
        reminders_bych = {}
        
        for recip in byrecip:
            reminders_pm = []
            
            for reminder in byrecip[recip]:
                if reminder["senderch"]=="":
                    reminders_pm.append(reminder)
                else:
                    if not reminder["senderch"] in reminders_bych:
                        reminders_bych[reminder["senderch"]] = []
                    reminders_bych[reminder["senderch"]].append(reminder)
            self.sendReminders(reminders_pm, recip, recip)
        
        for channel in reminders_bych:
            channelpms_bysender = {}
            
            for chreminder in reminders_bych[channel]:
                if not chreminder["sender"] in channelpms_bysender:
                    channelpms_bysender[chreminder["sender"]]=[]
                channelpms_bysender[chreminder["sender"]].append(chreminder)
            
            for recip in channelpms_bysender:
                self.sendReminders(channelpms_bysender[recip], channel, recip)
        
        # Delete now that it's sent
        for item in reminders:
            self.db.query("DELETE FROM `reminders` WHERE `id`=?", (item["id"],)).close()
    
    def sendReminders(self, reminders, target, nick):
        " Send a set of reminders of the same recipient, to them. Collapse down into one message."
        reminder_str = []
        for reminder in reminders:
            reminder_str.append(reminder["message"])
        reminder_str = ", ".join(reminder_str)
        if len(reminder_str)>0:
            self.bot.act_PRIVMSG(target, "%s: Reminder: %s" % (nick, reminder_str))
    
    def ondisable(self):
        self.disabled = True
    
    def remindat(self, args, prefix, trailing):
        prefixObj = self.bot.decodePrefix(prefix)
        
        replyTo = prefixObj.nick if not "#" in args[0] else args[0]
        
        # Lots of code borrowed from https://github.com/embolalia/willie/blob/master/willie/modules/remind.py
        cmd = self.bot.messageHasCommand([".at", ".remind"], trailing, True)
        if cmd:
            regex = re.compile(r'(\d+):(\d+)(?::(\d+))?([^\s\d]+)? (.*)')
            match = regex.match(cmd.args_str)
            
            try:
                hour, minute, second, tz, message = match.groups()
                message = message.strip()
                
                assert not message == ""
                
                hour = int(hour)
                minute = int(minute)
                if not second == None:
                    second = int(second)
                
            except:
                self.bot.act_PRIVMSG(replyTo, "%s: .at - Remind at a time. Example: .at 20:45EST Do your homework!" % prefixObj.nick)
                return
            
            now = datetime.now()
            remindAt = datetime.now()
            
            # if there was timezone, make sure the time we're reminding them at is relative to their timezone
            if not tz == None:
                try:
                    theirzone = pytz.timezone(Remind.translateZoneStr(tz))
                except:
                    self.bot.act_PRIVMSG(replyTo, "%s: I don't recognize the timezone '%s'." % (prefixObj.nick, tz))
                    return
                remindAt = theirzone.localize(remindAt, is_dst=Remind.is_dst(theirzone))
            
            # Set the hour and minute we'll remind them at today. If the ends up being in the past, we'll add a day alter
            remindAt = remindAt.replace(hour=hour).replace(minute=minute).replace(microsecond=0)
            
            # Set seconds
            if second == None:
                remindAt = remindAt.replace(second=0)
            else:
                remindAt = remindAt.replace(second=second)
            
            # if there was timezone, convert remindAt to our zone
            if not tz == None:
                try:
                    theirzone = pytz.timezone(Remind.translateZoneStr(tz))
                except:
                    self.bot.act_PRIVMSG(replyTo, "%s: I don't recognize the timezone '%s'." % (prefixObj.nick, tz))
                    return
                remindAt = remindAt.astimezone(pytz.timezone(self.config["mytimezone"])).replace(tzinfo=None)
            
            # Advance it a day if the time would have been earlier today
            while remindAt<now:
                remindAt += timedelta(days=1)
            
            timediff = remindAt-datetime.now()
            #self.bot.act_PRIVMSG(replyTo, "Time: %s" % str(remindAt))
            #self.bot.act_PRIVMSG(replyTo, "Diff: %s" % (timediff))
            
            # Save the reminder
            c = self.db.query("INSERT INTO `reminders` (`sender`, `senderch`, `when`, `message`) VALUES (?, ?, ?, ?)", (
                prefixObj.nick,
                args[0] if "#" in args[0] else "",
                remindAt,
                message
            ))
            c.close()
            
            diffHours = int(timediff.seconds / 60 / 60)
            diffMins= int((timediff.seconds-diffHours*60*60)/60)
            
            self.bot.act_PRIVMSG(replyTo, "%s: Ok, will do. Approx %sh%sm to go." % (prefixObj.nick, diffHours, diffMins))
    
    @staticmethod
    def is_dst(tz):
        now = pytz.utc.localize(datetime.utcnow())
        return now.astimezone(tz).dst() != timedelta(0)
    
    @staticmethod
    def translateZoneStr(zonestr):
        translations = {
            "EDT":"US/Eastern",
            "PDT":"America/Los_Angeles"
        }
        if zonestr in translations:
            return translations[zonestr]
        else:
            return zonestr
    
    def remindin(self, args, prefix, trailing):
        prefixObj = self.bot.decodePrefix(prefix)
        replyTo = prefixObj.nick if not "#" in args[0] else args[0]
        
        cmd = self.bot.messageHasCommand([".in", ".after"], trailing, True)
        if cmd:
            if len(cmd.args)==0:
                self.bot.act_PRIVMSG(replyTo, "%s: .in - Remind after x amount of time. Example: .in 1week5d2h1m Go fuck yourself" % 
                    (prefixObj.nick, diffHours, diffMins))
                return
            
            timepieces = re.compile(r'([0-9]+)([a-zA-Z]+)').findall(cmd.args[0])
            if len(timepieces)==0:
                self.bot.act_PRIVMSG(replyTo, "%s: .in - Remind after x amount of time. Example: .in 1week5d2h1m Go fuck yourself" % 
                    (prefixObj.nick, diffHours, diffMins))
                return
            
            delaySeconds = 0
            for match in timepieces:
                # ('30', 'm')
                if not match[1] in Remind.scaling:
                    self.bot.act_PRIVMSG(replyTo, "%s: Sorry, I don't understand the time unit '%s'" % (prefixObj.nick, match[1]))
                    return
                
                delaySeconds+=(Remind.scaling[match[1]] * int(match[0]))
            
            remindAt = datetime.now()+timedelta(seconds=delaySeconds)
            
            self.db.query("INSERT INTO `reminders` (`sender`, `senderch`, `when`, `message`) VALUES (?, ?, ?, ?)", (
                prefixObj.nick,
                args[0] if "#" in args[0] else "",
                remindAt,
                cmd.args_str[len(cmd.args[0]):].strip()
            )).close()
            
            hours = int(delaySeconds/60/60)
            minutes = int((delaySeconds-(hours*60*60))/60)
            
            self.bot.act_PRIVMSG(replyTo, "%s: Ok, talk to you in approx %sh%sm" % (prefixObj.nick, hours,minutes))

    scaling = {
        "years": 365.25 * 24 * 3600,
        "year": 365.25 * 24 * 3600,
        "yrs": 365.25 * 24 * 3600,
        "y": 365.25 * 24 * 3600,
        "months": 29.53059 * 24 * 3600,
        "month": 29.53059 * 24 * 3600,
        "mo": 29.53059 * 24 * 3600,
        "weeks": 7 * 24 * 3600,
        "week": 7 * 24 * 3600,
        "wks": 7 * 24 * 3600,
        "wk": 7 * 24 * 3600,
        "w": 7 * 24 * 3600,
        "days": 24 * 3600,
        "day": 24 * 3600,
        "d": 24 * 3600,
        "hours": 3600,
        "hour": 3600,
        "hrs": 3600,
        "hr": 3600,
        "h": 3600,
        "minutes": 60,
        "minute": 60,
        "mins": 60,
        "min": 60,
        "m": 60,
        "seconds": 1,
        "second": 1,
        "secs": 1,
        "sec": 1,
        "s": 1,
    }
