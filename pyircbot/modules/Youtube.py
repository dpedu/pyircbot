#!/usr/bin/env python
"""
.. module:: Youtube
	:synopsis: Search youtube with .youtube/.yt

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
from requests import get
import time

class Youtube(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.youtube)]
	
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
				self.bot.act_PRIVMSG(args[0], "http://youtu.be/%s :: %s" % (vid_id, self.get_video_description(vid_id)))
	
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