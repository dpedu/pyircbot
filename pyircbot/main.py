#!/usr/bin/env python3
import os
import sys
import logging
import yaml
from optparse import OptionParser
from core.pyircbot import PyIRCBot

if __name__ == "__main__":
	" logging level and facility "
	logging.basicConfig(level=logging.DEBUG, format="%(asctime)-15s %(levelname)-8s %(message)s")
	log = logging.getLogger('main')
	
	" parse command line args "
	parser = OptionParser()
	parser.add_option("-c", "--config", action="store", type="string", dest="config", help="Path to core config file")
	parser.add_option("-b", "--bot", action="store", type="string", dest="bot", help="Path to bot config file")
	
	(options, args) = parser.parse_args()
	
	log.debug(options)
	
	if not options.config:
		log.critical("No core config file specified (-c). Exiting.")
		sys.exit(0)
	if not options.bot:
		log.critical("No bot config file specified (-b). Exiting.")
		sys.exit(0)
	
	coreconfig = yaml.load(open(options.config, 'r'))
	botconfig = yaml.load(open(options.bot, 'r'))
	
	log.debug(coreconfig)
	log.debug(botconfig)
	
	bot = PyIRCBot(coreconfig, botconfig)
	try:
		bot.loop()
	except KeyboardInterrupt:
		bot.kill()
	
