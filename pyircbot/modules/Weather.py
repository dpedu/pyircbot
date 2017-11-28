#!/usr/bin/env python
"""
.. module:: Weather
    :synopsis: Fetch weather by location string

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, command
from requests import get
from pyircbot.modules.ModInfo import info


class Weather(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

        assert "get an API key" not in self.config["apikey"]

        self.login = self.bot.getBestModuleForService("login")
        try:
            assert self.login is not None
        except AssertionError as _ae:
            self.log.error("Weather: A 'login' service is required")
            return

        self.attr = self.bot.getBestModuleForService("attributes")
        try:
            assert self.attr is not None
        except AssertionError as _ae:  # NOQA
            self.log.error("Weather: An 'attributes' service is required")
            return

    @info("weather [location]          display the forecast", cmds=["weather", "w"])
    @command("weather", "w")
    def cmd_weather(self, msg, cmd):
        hasUnit = self.attr.get(msg.prefix.nick, "weather-unit")
        if hasUnit:
            hasUnit = hasUnit.upper()

        if len(cmd.args_str) > 0:
            self.send_weather(msg.args[0], msg.prefix.nick, cmd.args_str, hasUnit)
            return

        weatherZip = self.attr.get(msg.prefix.nick, "weather-zip")
        if weatherZip is None:
            self.bot.act_PRIVMSG(msg.args[0], "%s: you must set a location with .setloc" % (msg.prefix.nick,))
            return

        self.bot.act_PRIVMSG(msg.args[0], "%s: %s" % (msg.prefix.nick, self.getWeather(weatherZip, hasUnit)))

    @info("setloc <location>           set your home location for weather lookups", cmds=["setloc"])
    @command("setloc", allow_private=True)
    def cmd_setloc(self, msg, cmd):
        # if not cmd.args:
        #     self.bot.act_PRIVMSG(fromWho, ".setloc: set your location for weather lookup. Example: "
        #                                   ".setloc Rochester, NY")
        #     return
        reply_to = msg.args[0] if msg.args[0].startswith("#") else msg.prefix.nick
        weatherLoc = cmd.args_str
        try:
            result = self.getWeather(weatherLoc)  # NOQA
        except LocationNotSpecificException as lnse:
            self.bot.act_PRIVMSG(reply_to, "'%s': location not specific enough. Did you mean: %s" %
                                 (weatherLoc, self.alternates_to_str(lnse.alternates)))
            return
        except LocationException as le:
            self.bot.act_PRIVMSG(reply_to, "'%s': location not found: %s" % (weatherLoc, le))
            return

        if not self.login.check(msg.prefix.nick, msg.prefix.hostname):
            self.bot.act_PRIVMSG(reply_to, ".setloc: you need to be logged in to do that (try .login)")
            return

        self.attr.set(msg.prefix.nick, "weather-zip", weatherLoc)
        self.bot.act_PRIVMSG(reply_to, "Saved your location as %s"
                                              % self.attr.get(msg.prefix.nick, "weather-zip"))
        if self.attr.get(msg.prefix.nick, "weather-zip") is None:
            self.bot.act_PRIVMSG(reply_to, "Tip: choose C or F with .wunit <C/F>")

    @info("wunit <c|f>           set preferred weather unit", cmds=["wunit"])
    @command("wunit", allow_private=True)
    def cmd_wunit(self, msg, cmd):
        if cmd.args[0].lower() not in ['c', 'f']:
            return
        unit = cmd.args[0].lower()
        reply_to = msg.args[0] if msg.args[0].startswith("#") else msg.prefix.nick

        # if unit is None:
        #     self.bot.act_PRIVMSG(fromWho, ".wunit: set your preferred temperature unit to C or F")
        #     return

        if not self.login.check(msg.prefix.nick, msg.prefix.hostname):
            self.bot.act_PRIVMSG(reply_to, ".wunit: you need to be logged in to do that (try .login)")
            return

        self.attr.set(msg.prefix.nick, "weather-unit", unit.lower())
        self.bot.act_PRIVMSG(reply_to, "Saved your preferred unit as %s" % unit)

    def send_weather(self, target, hilight, location, units=None):
        try:
            self.bot.act_PRIVMSG(target, "%s: %s" % (hilight, self.getWeather(location, units)))
        except LocationNotSpecificException as lnse:
            self.bot.act_PRIVMSG(target, "'%s': location not specific enough. Did you mean: %s" %
                                 (location, self.alternates_to_str(lnse.alternates)))
        except LocationException as le:
            self.bot.act_PRIVMSG(target, "'%s': location not found: %s" % (location, le))

    def alternates_to_str(self, alternates):
        pieces = []
        for item in alternates:
            item_pieces = []
            for key in ["name", "state", "country_name"]:
                if key in item and len(item[key].strip()):
                    item_pieces.append(item[key])
            pieces.append(', '.join(item_pieces))
        return ' -- '.join(pieces)

    def getWeather(self, zipcode, unit=None):
        if unit is None:
            unit = self.config["defaultUnit"]
        unit = unit.lower()
        # Get data
        data = get("http://api.wunderground.com/api/%s/geolookup/conditions/forecast10day/q/%s.json" %
                   (self.config["apikey"], zipcode)).json()

        if "results" in data["response"]:
            raise LocationNotSpecificException(data["response"]["results"])
        if "error" in data["response"] and data["response"]["error"]["type"] == "querynotfound":
            raise LocationException

        # Build 5day
        fiveday = ""
        for item in data["forecast"]["simpleforecast"]["forecastday"][1:6]:
            fiveday += "%(day)s %(icon)s %(low)s-%(high)s°%(unit)s • " % {
                "unit": unit.upper(),
                "high": item["high"]["fahrenheit" if unit == "f" else "celsius"],
                "low": item["low"]["fahrenheit" if unit == "f" else "celsius"],
                "icon": self.icon2emoji(item["icon"]),
                "day": item["date"]["weekday_short"]
            }
        fiveday = fiveday[0:-3]

        # build wind speed
        wind_speed = data["current_observation"]["wind_mph"] if unit == "f" else data["current_observation"]["wind_kph"]
        wind_speed_gust = data["current_observation"]["wind_gust_mph"] if unit == "f" \
            else data["current_observation"]["wind_gust_mph"]
        if not wind_speed == wind_speed_gust and float(wind_speed_gust) > 0:
            wind_speed = "%s-%s" % (wind_speed, wind_speed_gust)
        else:
            wind_speed = "%s" % (wind_speed,)
        # return message
        return "\x02%(city)s, %(state)s:\x02 %(sky)s, \x02%(temp)s°%(unit)s\x02. %(wind_str)s %(wind_speed)smph " \
               "(%(wind_dir)s). \x02Next 5 days:\x02 %(fiveday)s" % {
                   "city": data["current_observation"]["display_location"]["city"],
                   "state": data["current_observation"]["display_location"]["state"],
                   "sky": data["forecast"]["simpleforecast"]["forecastday"][0]["conditions"],
                   "temp": int(data["current_observation"]["temp_f"]) if unit == "f"
                   else int(data["current_observation"]["temp_c"]),
                   "unit": unit.upper(),
                   "wind_str": self.shorten_windstr(data["current_observation"]["wind_string"].lower()),
                   "wind_speed": wind_speed,
                   "wind_dir": self.deg_to_arrow(int(data["current_observation"]["wind_degrees"])),
                   "fiveday": fiveday}

    def shorten_windstr(self, windstr):
        if "gusting" in windstr:
            return "Gusting"
        if "calm" in windstr:
            return "Calm"
        if "from the" in windstr.lower():
            return "Varying"
        return windstr[0:12]

    def icon2emoji(self,icon):
        if "partlycloudy" in icon or "mostlycloudy" in icon:
            return "⛅️"
        elif "cloudy" in icon:
            return "☁️"
        elif "rain" in icon:
            return "💧"
        elif "clear" in icon:
            return "☀️"
        elif "snow" in icon:
            return "❄️"
        else:
            return "(%s)" % icon

    def deg_to_arrow(self, deg):
        if deg > 335 or deg < 0:
            return "↑"
        elif deg > 292:
            return "⇖"
        elif deg > 247:
            return "←"
        elif deg > 202:
            return "⇙"
        elif deg > 157:
            return "↓"
        elif deg > 112:
            return "⇘"
        elif deg > 67:
            return "→"
        elif deg > 22:
            return "⇗"


class LocationException(Exception):
    pass


class LocationNotSpecificException(LocationException):
    def __init__(self, alternates):
        self.alternates  = alternates
    pass
