#!/usr/bin/env python
"""
.. module:: LinkTitler
    :synopsis: Fetch titles form links.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, hook
from requests import get
import re
import time
import praw  # TODO: enable/disable modules
import datetime
from requests import head
import html.parser
from threading import Thread


class LinkTitler(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.REQUEST_SIZE_LIMIT = 10 * 1024

    @hook("PRIVMSG")
    def searches(self, msg, cmd):
        t = Thread(target=self.doLinkTitle, args=(msg.args, msg.prefix.nick, msg.trailing))
        t.daemon = True
        t.start()

    def doLinkTitle(self, args, sender, trailing):
        # Youtube
        matches = re.compile(r'(?:youtube.*?(?:v=|/v/)|youtu\.be/|yooouuutuuube.*?id=)([-_a-z0-9]+)', re.I) \
            .findall(trailing)
        if matches:
            done = []
            for item in matches:
                if item not in done:
                    vidinfo = self.get_video_description(item)
                    if vidinfo:
                        self.bot.act_PRIVMSG(args[0], vidinfo)
                    done.append(item)
            return

        # reddit threads
        matches = re.compile(r'(?:reddit\.com/.*?comments/([a-zA-Z0-9]+)/|https?://(www\.)?redd.it/([a-zA-Z0-9]+))') \
            .findall(trailing)
        # Either [('', '', '2ibrz7')] or [('2ibrz7', '', '')]
        if matches:
            done = []
            for match in matches:
                submissionId = match[0]
                if submissionId == "":
                    submissionId = match[-1]
                if submissionId in done:
                    continue
                done.append(submissionId)
                r = praw.Reddit(**self.config["reddit"])
                submission = r.submission(id=submissionId)
                msg = "👽 \x02\x031,15REDDIT\x0f\x02 :: %(title)s \x02on \x02%(domain)s%(nsfw)s\x02 - points " \
                      "\x02%(points)s\x02 (%(percent)s↑) - comments \x02%(comments)s\x02 -  by \x02%(author)s\x02 on " \
                      "\x02%(date)s\x02" % {
                          "title": submission.title,
                          "domain": submission.domain,
                          "nsfw": "[NSFW]" if submission.over_18 else "",
                          "points": submission.ups,
                          "percent": "%s%%" % int(submission.upvote_ratio * 100),
                          "comments": submission.num_comments,
                          "author": submission.author.name,
                          "date": datetime.datetime.fromtimestamp(submission.created).strftime("%Y.%m.%d")
                      }
                self.bot.act_PRIVMSG(args[0], msg)
            return
        # reddit subscribers

        # subreddits

        # generic <title>
        matches = re.compile(r'(https?://([a-zA-Z0-9_\-\.]+/([A-Za-z0-9\-\._~:\/?#[]@!$&\'\(\)\*\+\,\;=]+)?))') \
            .findall(trailing)
        if matches:
            done = []
            for match in matches:
                if match[0] in done:
                    continue
                done.append(match[0])

                headers = self.url_headers(match[0])

                # Don't mess with unknown content types
                if "Content-Type" not in headers:
                    continue

                if "text/html" in headers["Content-Type"]:
                    # Fetch HTML title
                    title = self.url_htmltitle(match[0])
                    if title:
                        self.bot.act_PRIVMSG(args[0], "%s: \x02%s\x02" % (sender, title))
                else:
                    # Unknown types, just print type and size
                    self.bot.act_PRIVMSG(args[0], "%s: \x02%s\x02, %s" %
                                         (sender, headers["Content-Type"],
                                          self.nicesize(int(headers["Content-Length"])) if
                                          "Content-Length" in headers else "unknown size"))

            return

    def nicesize(self, numBytes):
        "Return kb or plain bytes"
        if numBytes > 1024:
            return "%skb" % str(int(numBytes / 1024))
        else:
            return "<1kb"

    def url_headers(self, url):
        """
        HEAD requests a url to check content type & length.
        Returns something like: {'type': 'image/jpeg', 'size': '90583'}"
        """
        self.log.info("url_headers(%s)" % (url,))
        resp = head(url=url, allow_redirects=True)
        return resp.headers

    def url_htmltitle(self, url):
        "Requests page html and returns title in a safe way"
        self.log.info("url_htmltitle(%s)" % (url,))
        resp = get(url=url, stream=True)
        # Fetch no more than first 10kb
        # if the title isn't seen by then, you're doing it wrong
        data = b""
        for chunk in resp.iter_content(1024):
            data += chunk
            if len(data) > self.REQUEST_SIZE_LIMIT:
                break

        data = data.decode('utf-8', "ignore")

        titleMatches = re.findall(r'<title>([^<]+)</title>', data, re.I)
        if len(titleMatches) > 0:  # and resp.status_code==200:
            h = html.parser.HTMLParser()
            title = h.unescape(titleMatches[0]).strip()
            if len(title) > 0:
                return title
        return None

    # For youtube
    def getISOdurationseconds(self, stamp):
        ISO_8601_period_rx = re.compile(
            'P'                       # designates a period
            '(?:(?P<years>\d+)Y)?'    # years
            '(?:(?P<months>\d+)M)?'   # months
            '(?:(?P<weeks>\d+)W)?'    # weeks
            '(?:(?P<days>\d+)D)?'     # days
            '(?:T'                    # time part must begin with a T
            '(?:(?P<hours>\d+)H)?'    # hours
            '(?:(?P<minutes>\d+)M)?'  # minutes
            '(?:(?P<seconds>\d+)S)?'  # seconds
            ')?'   # end of time part
        )  # http://stackoverflow.com/a/16742742
        return ISO_8601_period_rx.match(stamp).groupdict()

    def get_video_description(self, vid_id):
        apidata = get('https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id=%s'
                      '&key=%s' % (vid_id, self.config["youtube_api_key"])).json()

        if not apidata['pageInfo']['totalResults']:
            return

        video = apidata['items'][0]
        snippet = video["snippet"]
        duration = self.getISOdurationseconds(video["contentDetails"]["duration"])

        out = '\x02\x031,0You\x0f\x030,4Tube\x02\x0f :: \x02%s\x02' % snippet["title"]

        out += ' - length \x02'
        if duration["hours"] is not None:
            out += '%dh ' % int(duration["hours"])
        if duration["minutes"] is not None:
            out += '%dm ' % int(duration["minutes"])
        if duration["seconds"] is not None:
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
