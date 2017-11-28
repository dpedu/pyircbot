#!/usr/bin/env python
"""
.. module:: Youtube
    :synopsis: Search youtube with .youtube/.yt

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, command
from pyircbot.modules.ModInfo import info
from random import shuffle
from requests import get
import time
import re


class Youtube(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

    def getISOdurationseconds(self, stamp):
        ISO_8601_period_rx = re.compile(
            'P'   # designates a period
            '(?:(?P<years>\d+)Y)?'    # years
            '(?:(?P<months>\d+)M)?'   # months
            '(?:(?P<weeks>\d+)W)?'    # weeks
            '(?:(?P<days>\d+)D)?'     # days
            '(?:T'                    # time part begins with a T
            '(?:(?P<hours>\d+)H)?'    # hours
            '(?:(?P<minutes>\d+)M)?'  # minutes
            '(?:(?P<seconds>\d+)S)?'  # seconds
            ')?'   # end of time part
        )  # http://stackoverflow.com/a/16742742
        return ISO_8601_period_rx.match(stamp).groupdict()

    @info("yt                search for youtube videos", cmds=["yt", "youtube"])
    @command("yt", "youtube")
    def youtube(self, msg, cmd):
        j = get("https://www.googleapis.com/youtube/v3/search",
                params={"key": self.config["api_key"],
                        "part": "snippet",
                        "type": "video",
                        "maxResults": "25",
                        "safeSearch": self.config.get("safe_search", "none"),
                        "q": cmd.args_str}).json()

        if 'error' in j or len(j["items"]) == 0:
            self.bot.act_PRIVMSG(msg.args[0], "No results found.")
        else:
            shuffle(j['items'])
            vid_id = j["items"][0]['id']['videoId']
            self.bot.act_PRIVMSG(msg.args[0], "http://youtu.be/{} :: {}".format(vid_id,
                                                                                self.get_video_description(vid_id)))

    def get_video_description(self, vid_id):
        apidata = get('https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s'
                      '&key=%s' % (vid_id, self.config["api_key"])).json()

        if not apidata['pageInfo']['totalResults']:
            return

        video = apidata['items'][0]
        snippet = video["snippet"]
        duration = self.getISOdurationseconds(video["contentDetails"]["duration"])

        out = '\x02\x031,0You\x0f\x030,4Tube\x02\x0f :: \x02%s\x02' % snippet["title"]

        out += ' - \x02'
        if duration["hours"] is not None:
            out += '%dh ' % int(duration["hours"])
        if duration["minutes"] is not None:
            out += '%dm ' % int(duration["minutes"])
        out += "%ds\x02" % int(duration["seconds"])

        totalvotes = float(video["statistics"]["dislikeCount"]) + float(video["statistics"]["likeCount"])
        rating = float(video["statistics"]["likeCount"]) / totalvotes
        out += ' - rated \x02%.2f/5\x02' % round(rating * 5, 1)
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
