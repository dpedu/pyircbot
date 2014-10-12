#!/usr/bin/env python
"""
.. module:: LinkTitler
	:synopsis: Fetch titles form links.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from modulebase import ModuleBase,ModuleHook
from requests import get
import re
import time
import praw #TODO: enable/disable modules
import datetime
from requests import get
import html.parser
from threading import Thread

class LinkTitler(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.searches)]
	
	def searches(self, args, prefix, trailing):
		t = Thread(target=self.doLinkTitle, args=(args, prefix, trailing))
		t.daemon = True
		t.start()
	
	def doLinkTitle(self, args, prefix, trailing):
		sender = self.bot.decodePrefix(prefix)
		
		# Youtube
		matches = re.compile(r'(?:youtube.*?(?:v=|/v/)|youtu\.be/|yooouuutuuube.*?id=)([-_a-z0-9]+)', re.I).findall(trailing)
		if len(matches)>0:
			done = []
			for item in matches:
				if not item in done:
					self.bot.act_PRIVMSG(args[0], self.get_video_description(item))
					done.append(item)
			return
		
		# reddit threads
		matches = re.compile(r'(?:reddit\.com/.*?comments/([a-zA-Z0-9]+)/|https?://(www\.)?redd.it/([a-zA-Z0-9]+))').findall(trailing)
		# Either [('', '', '2ibrz7')] or [('2ibrz7', '', '')]
		if len(matches)>0:
			done = []
			for match in matches:
				submissionId = match[0]
				if submissionId=="":
					submissionId = match[-1]
				if submissionId in done:
					continue
				done.append(submissionId)
				# TODO configurable user agent
				r = praw.Reddit(self.config["agent"])
				submission = r.get_submission(submission_id = submissionId)
				#for i in range(0,18):
				#	self.bot.act_PRIVMSG(args[0], "\x031,%sTEST%s\x0f" %(i,i))
				msg = "👽 \x02\x031,15REDDIT\x0f\x02 :: %(title)s \x02on \x02%(domain)s%(nsfw)s\x02 - points \x02%(points)s\x02 (%(percent)s↑) - comments \x02%(comments)s\x02 -  by \x02%(author)s\x02 on \x02%(date)s\x02" % {
					"title":submission.title,
					"domain":submission.domain,
					"nsfw": "[NSFW]" if submission.over_18 else "",
					"points":submission.ups,
					"percent":"%s%%" % int(submission.upvote_ratio*100),
					"comments":submission.num_comments,
					"author":submission.author.name,
					"date":datetime.datetime.fromtimestamp(submission.created).strftime("%Y.%m.%d")
				}
				self.bot.act_PRIVMSG(args[0], msg)
			return
		# reddit subscribers
		
		# subreddits
		
		# generic <title>
		matches = re.compile(r'(https?://([a-zA-Z0-9_\-\.]+/([^ ]+)?))').findall(trailing)
		if len(matches)>0:
			done=[]
			for match in matches:
				if match[0] in done:
					continue
				done.append(match[0])
				d = get(match[0])
				titleMatches = re.findall(r'<title>([^<]+)</title>', d.text, re.I)
				if len(titleMatches)>0 and d.status_code==200:
					h = html.parser.HTMLParser()
					title = h.unescape(titleMatches[0]).strip()
					if len(title)>0:
						self.bot.act_PRIVMSG(args[0], "%s: \x02%s\x02" % (sender.nick, title))
			return
	
	# For youtbue
	def get_video_description(self, vid_id):
		j = get("http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc" % vid_id).json()
		if j.get('error'):
			return
		j = j['data']
		out = '\x02\x031,0You\x0f\x030,4Tube\x02\x0f :: \x02%s\x02' % j['title']
		if not j.get('duration'):
			return out
		out += ' - length \x02'
		length = j['duration']
		if length / 3600:  # > 1 hour
			out += '%dh ' % (length / 3600)
		if length / 60:
			out += '%dm ' % (length / 60 % 60)
		out += "%ds\x02" % (length % 60)
		if 'rating' in j:
			out += ' - rated \x02%.2f/5.0\x02 (%d)' % (j['rating'],
													   j['ratingCount'])
		if 'viewCount' in j:
			out += ' - \x02%s\x02 views' % self.group_int_digits(j['viewCount'])
		upload_time = time.strptime(j['uploaded'], "%Y-%m-%dT%H:%M:%S.000Z")
		out += ' - \x02%s\x02 on \x02%s\x02' % (
							j['uploader'], time.strftime("%Y.%m.%d", upload_time))
		if 'contentRating' in j:
			out += ' - \x034NSFW\x02'
		return out
	def group_int_digits(self, number, delimiter=',', grouping=3):
		base = str(number).strip()
		builder = []
		while base:
			builder.append(base[-grouping:])
			base = base[:-grouping]
		builder.reverse()
		return delimiter.join(builder)
