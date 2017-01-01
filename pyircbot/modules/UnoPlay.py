"""
.. module:: UnoPlay
    :synopsis: Plays the Uno card game against the popular Eggdrop script "Color Uno"

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook
from random import randint
import time
import re
from operator import itemgetter
from threading import Thread


class UnoPlay(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.servicesModule = self.bot.getmodulebyname("Services")
        self.hooks = [ModuleHook("PRIVMSG", self.unoplay),
                      ModuleHook("PRIVMSG", self.trigger),
                      ModuleHook("NOTICE", self.decklisten)]
        self.current_card = None
        self.shouldgo = False
        self.has_drawn = False
        self.has_joined = False
        self.games_played = 0
        self.cards = []

    def trigger(self, args, prefix, trailing):
        if trailing.startswith("["):  # anti-znc buffer playback
            return
        if self.config["enable_trigger"] and "!jo" in trailing:
            self.bot.act_PRIVMSG(self.config["unochannel"], "jo")
        elif trailing == "jo":
            # Reset streak counter & join if another human joins
            self.games_played = 0
            self.join_game()

    def join_game(self):
        if not self.has_joined:
            self.sleep("joingame")
            self.has_joined = True
            self.bot.act_PRIVMSG(self.config["unochannel"], "jo")

    def unoplay(self, args, prefix, trailing):
        if trailing.startswith("["):  # anti-znc buffer playback
            return

        trailing = self.stripcolors(trailing)

        if self.config["unobot"] not in prefix:
            return

        # Parse card from beginning message
        # See if we play first
        if "plays first..." in trailing:
            message = trailing.split("The top card is")[1]
            self.log.debug(">> we play first!")
            self.current_card = self.parsecard(message)
            self.log.debug(">> top card: %s" % str(self.current_card))

            if self.bot.get_nick() in trailing:
                self.shouldgo = True

        # See if someone passed to us
        if "passes" in trailing and self.bot.get_nick() in trailing:
            self.shouldgo = True

        # Play after someone was droppped
        if "continuing with" in trailing and self.bot.get_nick() in trailing:
            self.shouldgo = True

        # Parse misc played cards
        # bug
        if " plays  " in trailing:
            message = trailing.split(" plays  ")[1].split("   ")[0]
            self.current_card = self.parsecard(message)
            self.log.debug(">> current card: %s" % str(self.current_card))

        # After someone plays to us
        if "to %s" % self.bot.get_nick() in trailing:
            self.shouldgo = True

        # After color change
        if "play continues with " in trailing:
            color = trailing.split(" chose  ")[1].split(" , ")[0].strip()
            self.current_card[2]['color'] = {'Blue': 'b', 'Red': 'r', 'Yellow': 'y', 'Green': 'g'}[color]
            self.current_card[2]['number'] = -1
            self.current_card[2]['type'] = None

            self.log.debug("Color changed to %s " % self.current_card[2]['color'])

        # After color change by bot
        if "Current player " in trailing and "and chooses" in trailing:
            color = trailing.split(" and chooses  ")[1].split(" Current ")[0].strip()
            self.current_card[2]['color'] = {'Blue': 'b', 'Red': 'r', 'Yellow': 'y', 'Green': 'g'}[color]
            self.current_card[2]['number'] = -1
            self.current_card[2]['type'] = None
            self.log.debug("Color changed to %s " % self.current_card[2]['color'])
            if "urrent player %s" % self.bot.get_nick() in trailing:
                self.shouldgo = True

        # After color change to us
        if "play continues with %s" % self.bot.get_nick() in trailing:
            self.shouldgo = True

        # We need to choose a color
        if "hoose a color %s" % self.bot.get_nick() in trailing:
            self.pickcolor()

        # Reset
        if " by Marky" in trailing or "cards played in" in trailing:
            self.log.debug(">> Reset")
            self.current_card = None
            self.shouldgo = False
            self.has_drawn = False
            self.has_joined = False
            self.cards = []

        if self.config["enable_autojoin"]:
            if "to join uno" in trailing:
                if self.games_played >= self.config["streak_max"]:
                    self.games_played = 0
                    return
                else:
                    self.join_game()

    def send_later(self, channel, msg, area):
        Thread(target=self._send_later, args=(self.bot.act_PRIVMSG, (channel, msg, ), area)).start()

    def _send_later(self, method, args, kwargs, area):
        self.sleep(area)
        method(*args, **kwargs)

    def sleep(self, area):
        if self.config["enable_delays"]:
            sleep_min, sleep_max = self.config["delay_{}".format(area)]
            sleep_time = randint(sleep_min * 10, sleep_max * 10) / 10
            self.log.debug("Sleeping {}s for {}".format(sleep_time, area))
            time.sleep(sleep_time)

    def pickcolor(self):
        mycolors = {"r": 0, "g": 0, "b": 0, "y": 0}
        for card in self.cards:
            if card[2]["color"] in mycolors.keys():
                mycolors[card[2]["color"]] += 1

        mycolors = sorted(mycolors.items(), key=itemgetter(1))
        mycolors.reverse()

        self.log.debug("Sorted: %s" % str(mycolors))

        self.sleep("beforepickcolor")
        self.bot.act_PRIVMSG(self.config["unochannel"], "co %s" % mycolors[0][0])

    def taketurn(self):
        self.shouldgo = False
        move = self.getbestmove()

        if move is None:
            if self.has_drawn:
                self.has_drawn = False
                self.shouldgo = False
                self.bot.act_PRIVMSG(self.config["unochannel"], "pa")
            else:
                self.has_drawn = True
                self.shouldgo = True
                self.sleep("beforedraw")
                self.bot.act_PRIVMSG(self.config["unochannel"], "dr")
            return

        self.has_drawn = False
        if self.config["enable_randomhuman"]:
            if randint(1, self.config["randomhuman_chance"]) == 1:
                self.bot.act_PRIVMSG(self.config["unochannel"], "ct")
                if self.config["enable_delays"]:
                    time.sleep(self.config["randomhuman_sleep"])
        self.sleep("beforemove")
        self.log.debug(">> playing %s" % move[0])
        self.playcard(move[0])

    def getbestmove(self):
        # Play anything thats not a wild
        for card in self.cards:
            # Skip wilds for now
            if card[0] in ["wd4", "w"]:
                continue
            if self.validate(card, self.current_card):
                return card

        # Play anything
        for card in self.cards:
            if self.validate(card, self.current_card):
                return card

        # Give up
        return None

    def validate(self, newcard, basecard):
        nc = newcard[2]
        bc = basecard[2]

        # Wilds can always be played
        if nc["type"] in ["wd4", "w"]:
            return True

        # Color matches can always be played
        if nc["color"] == bc["color"]:
            return True

        # Matching numbers are ok
        if nc["type"] == "num" and bc["type"] == "num" and nc["number"] == bc["number"]:
            return True

        # type matches can always be played unless its a number
        if nc["type"] == bc["type"] and not bc["type"] == "num":
            return True

        self.log.debug("invalid: %s on %s)" % (nc, bc))

        return False

    def playcard(self, card):
        self.bot.act_PRIVMSG(self.config["unochannel"], "pl %s" % card)

    def decklisten(self, args, prefix, trailing):
        if trailing.startswith("["):  # anti-znc buffer playback
            return
        if self.config["unobot"] not in prefix:
            return

        trailing = self.stripcolors(trailing)

        cards = []

        for carddata in trailing.split("   "):
            carddata = carddata.strip()
            cards.append(self.parsecard(carddata))
        cards.sort(key=lambda tup: tup[1])
        cards.reverse()

        self.cards = cards

        self.log.debug(cards)

        if self.shouldgo:
            self.shouldgo = False
            self.taketurn()

    def parsecard(self, input):
        # returns a card, weight tuple
        self.log.debug("Parse %s" % input)
        # Colors
        colors = {
            'r': 'Red',
            'y': 'Yellow',
            'b': 'Blue',
            'g': 'Green'
        }
        # cards that don't have a color
        uncolored_cards = ['wd4', 'w']
        # types of cards
        card_types = [
            ('wd4', 'Draw Four'),
            ('w', 'WI LD'),
            ('d2', 'Two'),
            ('r', 'Reverse'),
            ('s', 'Skip')
        ]

        weights = {
            'wd4': 30,
            'w': 20,
            'd2': 15,
            'r': 14,
            's': 14
        }

        card = ""
        weight = 0
        cardinfo = {"type": None, "color": None, "number": None}

        for duo in card_types:
            key = duo[0]
            value = duo[1]
            if value in input:
                if key in uncolored_cards:
                    cardinfo["type"] = key
                    return (key, weights[key], cardinfo)
                else:
                    card = key
                    if key in weights:
                        weight = weights[key]
                    break

        cardinfo["type"] = card

        if card == "":
            # If we're here, the card has to be a number
            # ghetto parse it
            cardnumstr = ""
            for i in input:
                try:
                    cardnumstr += str(int(i))
                except:
                    pass

            card = cardnumstr
            weight = int(cardnumstr)

            cardinfo["type"] = "num"
            cardinfo["number"] = weight

        for color in colors:
            if colors[color] in input:
                cardinfo["color"] = color
                return (color + card, weight, cardinfo)

    def stripcolors(self, input):
        return re.sub(r'\\x0([23])(([0-9]{1,2}((,[0-9]{1,2})?))?)', '', repr(input))[1:-1]

    # def ondisable(self):
    #     pass
