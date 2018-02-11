#!/usr/bin/env python3

"""
.. module::SMS
    :synopsis: SMS client script (requires Twilio account)
"""

from time import time
from math import floor
from pyircbot.modulebase import ModuleBase, regex
from pyircbot.modules.ModInfo import info
import cherrypy
from threading import Thread
from twilio.rest import Client


class Api(object):
    def __init__(self, mod):
        self.mod = mod

    @cherrypy.expose
    def gotsms(self, *args, **kwargs):
        """
        Twilio webhook listener
        """

        """
        Example payload:
        {'To': '+11234567890',
         'ToCity': 'ALBERTVILLE',
         'ToState': 'AL',
         'ToZip': '35951',
         'ToCountry': 'US,
         'NumMedia': '1',
         'MediaContentType0': 'image/jpeg',
         'MediaUrl0': 'https://api.twilio.com/xxx',
         'From': '+11234567890',
         'FromCity': 'ROCHESTER',
         'FromState': 'NY',
         'FromZip': '14622',
         'FromCountry': 'US',
         'Body': 'Lol',
         'NumSegments': '1',
         'SmsStatus': 'received',
         'SmsSid': 'xxx',
         'SmsMessageSid': 'xxx',
         'MessageSid': 'xxx',
         'AccountSid': 'xxx',
         'MessagingServiceSid': 'xxx',
         'ApiVersion': '2010-04-01'}
        """
        attachments = []
        medias = int(kwargs["NumMedia"])
        while medias > 0:
            medias -= 1
            attachments.append((kwargs["MediaContentType{}".format(medias)], kwargs["MediaUrl{}".format(medias)], ))

        self.mod.got_text(kwargs["From"], kwargs["Body"], attachments=attachments)
        yield ''


class SMS(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.apithread = None
        self.twilio = Client(self.config["account_sid"], self.config["auth_token"])

        # limit-related vars
        # How many messages can be bursted
        self.bucket_max = int(self.config["limit"]["max"])
        # burst bucket, initial value is 1 or half the max, whichever is more
        self.bucket = max(1, self.bucket_max / 2)
        # how often the bucket has 1 item added
        self.bucket_period = int(self.config["limit"]["period"])
        # last time the burst bucket was filled
        self.bucket_lastfill = int(time())

    def check_rate_limit(self):
        """
        Rate limiting via a 'burst bucket'. This method is called before sending and returns true or false depending on
        if the action is allowed.
        """

        # First, update the bucket
        # Check if $period time has passed since the bucket was filled
        since_fill = int(time()) - self.bucket_lastfill
        if since_fill > self.bucket_period:
            # How many complete points are credited
            fills = floor(since_fill / self.bucket_period)
            self.bucket += fills
            if self.bucket > self.bucket_max:
                self.bucket = self.bucket_max
            # Advance the lastfill time appropriately
            self.bucket_lastfill += self.bucket_period * fills

        if self.bucket >= 1:
            self.bucket -= 1
            return True
        return False

    def api(self):
        """
        Run the webhook listener and block
        """
        api = Api(self)
        cherrypy.config.update({
            # 'sessionFilter.on': True,
            'tools.sessions.on': False,
            'tools.sessions.locking': 'explicit',
            # 'tools.sessions.timeout': 525600,
            'request.show_tracebacks': True,
            'server.socket_port': self.config.get("api_port"),
            'server.thread_pool': 1,
            'server.socket_host': '0.0.0.0',
            'server.show_tracebacks': True,
            'server.socket_timeout': 10,
            'log.screen': False,
            'engine.autoreload.on': False})
        cherrypy.tree.mount(api, '/app/', {})
        cherrypy.engine.start()
        cherrypy.engine.block()

    def onenable(self):
        """
        If needed, create an API and run it
        """
        if self.apithread is None and self.config.get("api_port") > 0:
            self.apithread = Thread(target=self.api, daemon=True)
            self.apithread.start()

    def ondisable(self):
        """
        Shut down the api
        """
        cherrypy.engine.exit()

    @info("text-<name>", "text somebody on the VIP list", cmds=["text"])
    @regex(r'(?:^\.text\-([a-zA-Z0-9]+)(?:\s+(.+))?)', types=['PRIVMSG'])
    def cmd_text(self, msg, match):
        """
        Text somebody
        """
        contact, message = match.groups()
        contact = contact.lower()

        if msg.args[0].lower() != self.config["channel"].lower():
            return  # invalid channel
        if message is None:
            return  # TODO help text
        if contact not in self.config["contacts"].keys():
            return  # TODO invalid contact

        if self.config["limit"]["enable"]:
            if not self.check_rate_limit():
                self.bot.act_PRIVMSG(msg.args[0], "Sorry, try again later")
                return

        try:
            self.twilio.api.account.messages.create(to=self.config["contacts"][contact],
                                                    from_=self.config["number"],
                                                    body="{} <{}>: {}".format(msg.args[0],
                                                                              msg.prefix.nick,
                                                                              msg.trailing[7 + len(contact):].strip()))
        except Exception as e:
            self.bot.act_PRIVMSG(msg.args[0], "Could not send message: {}".format(repr(e)))
        else:
            self.bot.act_PRIVMSG(msg.args[0], "Message sent.")

    def got_text(self, sender, body, attachments=None):
        """
        Webhook callback to react to a message

        :param sender: number that sent the message, like +10000000000
        :type sender: str
        :param body: body text of the sms/mms
        :type body: str
        :param attachments: if mms, any attachments as a list of (mime, url) tuples
        :type attachments: list
        """
        name = None
        for contact, number in self.config["contacts"].items():
            if number == sender:
                name = contact

        if name is None:
            name = sender

        body = body.strip()
        if body:
            self.bot.act_PRIVMSG(self.config["channel"], "SMS from {}: {}".format(name, body))

        if attachments:
            for mime, url in attachments[0:3]:
                self.bot.act_PRIVMSG(self.config["channel"], "MMS from {}: {} ({})".format(name, url, mime))
