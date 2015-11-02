#!/usr/bin/env python
"""
.. module:: Weather
    :synopsis: Fetch weather by location string

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
from requests import get
from urllib.parse import urlencode

class Weather(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName);
        
        assert not "get an API key" in self.config["apikey"]
        
        self.login = self.bot.getBestModuleForService("login")
        try:
            assert not self.login == None
        except AssertionError as _ae:
            self.log.error("Weather: A 'login' service is required")
            return
        
        self.attr = self.bot.getBestModuleForService("attributes")
        try:
            assert not self.attr == None
        except AssertionError as _ae:
            self.log.error("Weather: An 'attributes' service is required")
            return
        
        self.hooks=[ModuleHook("PRIVMSG", self.weather)]
    
    def weather(self, args, prefix, trailing):
        prefixObj = self.bot.decodePrefix(prefix)
        fromWho = prefixObj.nick
        
        replyTo = args[0] if "#" in args[0] else fromWho
        
        hasUnit = self.attr.get(fromWho, "weather-unit")
        if hasUnit:
            hasUnit = hasUnit.upper()
        
        cmd = self.bot.messageHasCommand([".w", ".weather"], trailing)
        if cmd:
            if len(cmd.args_str)>0:
                self.send_weather(replyTo, fromWho, cmd.args_str, hasUnit)
                return
            
            weatherZip = self.attr.get(fromWho, "weather-zip")
            if weatherZip == None:
                self.bot.act_PRIVMSG(replyTo, "%s: you must set a location with .setloc" % (fromWho,))
                return
            
            self.bot.act_PRIVMSG(replyTo, "%s: %s" % (fromWho, self.getWeather(weatherZip, hasUnit)))
        
        cmd = self.bot.messageHasCommand(".setloc", trailing)
        if cmd and not args[0]=="#":
            
            if len(cmd.args)==0:
                self.bot.act_PRIVMSG(fromWho, ".setloc: set your location for weather lookup. Example: .setloc Rochester, NY")
                return
            
            weatherLoc = cmd.args_str
            
            try:
                result = self.getWeather(weatherLoc)
            except LocationNotSpecificException as lnse:
                self.bot.act_PRIVMSG(fromWho, "'%s': location not specific enough. Did you mean: %s" % (weatherLoc, self.alternates_to_str(lnse.alternates)))
                return
            except LocationException as le:
                self.bot.act_PRIVMSG(fromWho, "'%s': location not found" % weatherLoc)
                return
                
            if not self.login.check(prefixObj.nick, prefixObj.hostname):
                self.bot.act_PRIVMSG(fromWho, ".setloc: you need to be logged in to do that (try .login)")
                return
            
            self.attr.set(fromWho, "weather-zip", weatherLoc)
            self.bot.act_PRIVMSG(fromWho, "Saved your location as %s" % self.attr.get(fromWho, "weather-zip"))
            if self.attr.get(fromWho, "weather-zip")==None:
                self.bot.act_PRIVMSG(fromWho, "Tip: choose C or F with .wunit <C/F>")
        
        cmd = self.bot.messageHasCommand(".wunit", trailing)
        if cmd and not args[0]=="#":
            unit = None
            try:
                assert cmd.args[0].lower() in ['c', 'f']
                unit = cmd.args[0]
            except:
                pass
                
            if unit == None:
                self.bot.act_PRIVMSG(fromWho, ".wunit: set your preferred temperature unit to C or F")
                return
                
            if not self.login.check(prefixObj.nick, prefixObj.hostname):
                self.bot.act_PRIVMSG(fromWho, ".wunit: you need to be logged in to do that (try .login)")
                return
            
            self.attr.set(fromWho, "weather-unit", unit.lower())
            self.bot.act_PRIVMSG(fromWho, "Saved your preferred unit as %s" % self.attr.get(fromWho, "weather-unit").upper())
    
    def send_weather(self, target, hilight, location, units=None):
        try:
            self.bot.act_PRIVMSG(target, "%s: %s" % (hilight, self.getWeather(location, units)))
        except LocationNotSpecificException as lnse:
            self.bot.act_PRIVMSG(target, "'%s': location not specific enough. Did you mean: %s" % (location, self.alternates_to_str(lnse.alternates)))
        except LocationException as le:
            self.bot.act_PRIVMSG(target, "'%s': location not found" % location)
    
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
        if unit==None:
            unit = self.config["defaultUnit"]
        unit = unit.lower()
        # Get data
        data = get("http://api.wunderground.com/api/%s/geolookup/conditions/forecast10day/q/%s.json" % (self.config["apikey"], zipcode)).json()
        
        if "results" in data["response"]:
            raise LocationNotSpecificException(data["response"]["results"])
        if "error" in data["response"] and data["response"]["error"]["type"]=="querynotfound":
            raise LocationException
        
        # Build 5day
        fiveday = ""
        for item in data["forecast"]["simpleforecast"]["forecastday"][1:6]:
            fiveday += "%(day)s %(icon)s %(low)s-%(high)s°%(unit)s • " % {
                "unit":unit.upper(),
                "high":item["high"]["fahrenheit" if unit=="f" else "celsius"],
                "low":item["low"]["fahrenheit" if unit=="f" else "celsius"],
                "icon":self.icon2emoji(item["icon"]),
                "day":item["date"]["weekday_short"]
            }
        fiveday=fiveday[0:-3]
        
         # build wind speed 
        wind_speed = data["current_observation"]["wind_mph"] if unit=="f" else data["current_observation"]["wind_kph"]
        wind_speed_gust = data["current_observation"]["wind_gust_mph"] if unit=="f" else data["current_observation"]["wind_gust_mph"]
        if not wind_speed==wind_speed_gust and float(wind_speed_gust)>0:
            wind_speed = "%s-%s" % (wind_speed, wind_speed_gust)
        else:
            wind_speed = "%s" % (wind_speed,)
        # return message
        return "\x02%(city)s, %(state)s:\x02 %(sky)s, \x02%(temp)s°%(unit)s\x02. %(wind_str)s %(wind_speed)smph (%(wind_dir)s). \x02Next 5 days:\x02 %(fiveday)s" % {
            "city": data["current_observation"]["display_location"]["city"],
            "state": data["current_observation"]["display_location"]["state"],
            "sky": data["forecast"]["simpleforecast"]["forecastday"][0]["conditions"],
            "temp": int(data["current_observation"]["temp_f"]) if unit=="f" else int(data["current_observation"]["temp_c"]),
            "unit": unit.upper(),
            "wind_str": self.shorten_windstr(data["current_observation"]["wind_string"].lower()),
            "wind_speed": wind_speed,
            "wind_dir": self.deg_to_arrow(int(data["current_observation"]["wind_degrees"])),
            "fiveday":fiveday
        }
    
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