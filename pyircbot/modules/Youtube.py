#!/usr/bin/env python
"""
.. module:: Youtube
    :synopsis: Search youtube with .youtube/.yt

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
from requests import get
import time
import re

class Youtube(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName);
        self.hooks=[ModuleHook("PRIVMSG", self.youtube)]
    
    def getISOdurationseconds(self, stamp):
        ISO_8601_period_rx = re.compile(
            'P'   # designates a period
            '(?:(?P<years>\d+)Y)?'   # years
            '(?:(?P<months>\d+)M)?'  # months
            '(?:(?P<weeks>\d+)W)?'   # weeks
            '(?:(?P<days>\d+)D)?'    # days
            '(?:T' # time part must begin with a T
            '(?:(?P<hours>\d+)H)?'   # hours
            '(?:(?P<minutes>\d+)M)?' # minutes
            '(?:(?P<seconds>\d+)S)?' # seconds
            ')?'   # end of time part
        ) # http://stackoverflow.com/a/16742742
        return ISO_8601_period_rx.match(stamp).groupdict()
    
    def youtube(self, args, prefix, trailing):
        
        cmd = self.bot.messageHasCommand(".youtube", trailing)
        if not cmd:
            cmd = self.bot.messageHasCommand(".yt", trailing)
        if cmd and args[0][0:1]=="#":
            #TOTO search youtube
            if cmd.args_str.strip() =="":
                self.bot.act_PRIVMSG(args[0], '.youtube <query> -- returns the first YouTube search result for <query>')
                return
            j = get("http://gdata.youtube.com/feeds/api/videos?v=2&alt=jsonc&max-results=1", params={"q":trailing}).json()
            if 'error' in j or j['data']['totalItems']==0:
                self.bot.act_PRIVMSG(args[0], "YouTube: No results found.")
            else:
                vid_id = j['data']['items'][0]['id']
                vidinfo = self.get_video_description(vid_id)
                if vidinfo:
                    self.bot.act_PRIVMSG(args[0], "http://youtu.be/%s :: %s" % (vid_id, vidinfo))
    
    def get_video_description(self, vid_id):
        apidata = get('https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s&key=%s' % (vid_id, self.config["api_key"])).json()
        
        if not apidata['pageInfo']['totalResults']:
            return
        
        video = apidata['items'][0]
        snippet = video["snippet"]
        duration = self.getISOdurationseconds(video["contentDetails"]["duration"])
        
        out = '\x02\x031,0You\x0f\x030,4Tube\x02\x0f :: \x02%s\x02' % snippet["title"]
        
        out += ' - length \x02'
        if duration["hours"]!=None:
            out += '%dh ' % int(duration["hours"])
        if duration["minutes"]!=None:
            out += '%dm ' % int(duration["minutes"])
        out += "%ds\x02" % int(duration["seconds"])
        
        totalvotes = float(video["statistics"]["dislikeCount"])+float(video["statistics"]["likeCount"])
        rating = float(video["statistics"]["likeCount"]) / totalvotes
        out += ' - rated \x02%.2f/5\x02' % round(rating*5,1)
        out += ' - \x02%s\x02 views' % self.group_int_digits(video["statistics"]["viewCount"])
        upload_time = time.strptime(snippet['publishedAt'], "%Y-%m-%dT%H:%M:%S.000Z")
        out += ' - by \x02%s\x02 on \x02%s\x02' % (snippet['channelTitle'], time.strftime("%Y.%m.%d", upload_time))
        
        return out
   
    def group_int_digits(self, number, delimiter=',', grouping=3):
        base = str(number).strip()
        builder = []
        while base:
            builder.append(base[-grouping:])
            base = base[:-grouping]
        builder.reverse()
        return delimiter.join(builder)
