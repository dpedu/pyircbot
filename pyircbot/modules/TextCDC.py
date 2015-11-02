#!/usr/bin/env python

"""
.. module::TextCDC
    :synopsis: Text Chrisdotcode, right now.
.. moduleauthor::Nick Krichevsky <nick@ollien.com>
"""

import smtplib
import imaplib
from threading import Timer
from pyircbot.modulebase import ModuleBase, ModuleHook

COMMAND_PREFIX = ".text-"

class TextCDC(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks.append(ModuleHook("PRIVMSG",self.handleMessage))    
        self.loadConfig()
        self.prefixes = [person for person in self.config["people"]]
        self.bot = bot
        self.timer = None
        self.setupTimer()

    def ondisable(self):
        if self.timer != None:
            self.timer.cancel()

    def handleMessage(self, args, prefix, trailing):
        channel = args[0]
        p = self.bot.decodePrefix(prefix)
        if self.bot.messageHasCommand(".textstatus", trailing):
            #self.bot.act_PRIVMSG(channel, "POP: %s" % "Good" if setupPop() != None else "Failed.")
            self.bot.act_PRIVMSG(channel, "SMTP: %s" % "Good" if setupSMTP() != None else "Failed.")
        for prefix in self.prefixes:
            if self.bot.messageHasCommand(COMMAND_PREFIX + prefix, trailing):
                email = self.config["people"][prefix]["email-addr"]
                message = ' '.join(trailing.split(" ")[1:])
                smtp = self.setupSMTP()
                try:
                    smtp.sendmail(self.config["account"]["auth"]["username"], email, "Subject:\n\n%s -%s" % (message, p.nick))
                    smtp.quit()
                    self.bot.act_PRIVMSG(channel, "Message sent.")
                except Exception as e:
                    self.bot.log.error(str(e))
                    self.bot.act_PRIVMSG(channel, "An SMTP Error has Occured")

    def setupIMAP(self):
        imapObj = None
        if self.config["account"]["imap"]["ssl"]:
            imapObj = imaplib.IMAP4_SSL(self.config["account"]["imap"]["host"], self.config["account"]["imap"]["port"])
        else:
            imapObj = imaplib.IMAP4(self.config["account"]["imap"]["host"], self.config["account"]["imap"]["port"])
        imapObj.login(self.config["account"]["auth"]["username"], self.config["account"]["auth"]["password"])
        resp = imapObj.select("INBOX")
        if resp[0] == "OK":
            return imapObj
        else:
            return None

    def setupSMTP(self):
        smtpObj = None
        if self.config["account"]["smtp"]["ssl"]:
            smtpObj = smtplib.SMTP_SSL(self.config["account"]["smtp"]["host"], self.config["account"]["smtp"]["port"])    
        else:
            smtpObj = smtplib.SMTP_SSL(self.config["account"]["smtp"]["host"], self.config["account"]["smtp"]["port"])
        if self.config["account"]["smtp"]["authentication"]:
            resp = smtpObj.login(self.config["account"]["auth"]["username"], self.config["account"]["auth"]["password"])
            if resp[0] == 235:
                return smtpObj
            else:
                return None
        else:
            resp = smtpObj.connect()
            if resp[0] == 220:
                return smtpObj
            else:
                return None
    
    def setupTimer(self):
            self.timer = Timer(self.config["interval"], self.checkMail, [self.bot, self.config["people"], self.config["output-channels"]],{})
            self.timer.start()
    
    def checkMail(self, bot, people, channels, imapObj = None):
        try:
            if imapObj == None:
                imapObj = self.setupIMAP()
            for person in people:
                emailAddr = people[person]["email-addr"]
                result = imapObj.search(None, "(FROM \"%s\")" % emailAddr)
                if (result[0] == "OK"):
                    messageIds = result[1][0].decode("utf-8")
                    if len(messageIds) > 0:
                        messageIds = messageIds.split(" ")
                        for messageId in messageIds:
                            message = imapObj.fetch(messageId, "BODY[TEXT]")
                            if (message[0] == "OK"):
                                messageText = message[1][0][1].decode("utf-8").split("-----Original Message-----")[0].rstrip()
                                for channel in channels: 
                                    bot.act_PRIVMSG(channel, "Message from %s: %s" % (person, messageText))
                                imapObj.store(messageId, "+FLAGS", "\\Deleted")
                            else:
                                raise Exception("SMTP Error. Status was %s, expected OK" % message[0])
            imapObj.logout()
            self.setupTimer()
        except Exception as e:
            if imapObj != None:
                imapObj.logout()
            self.setupTimer()
            raise e    
