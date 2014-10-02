"""
.. module:: ModuleBase
	:synopsis: Base class that modules will extend

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import logging
import os
import yaml

class ModuleBase:
	" All modules must extend this class. "
	def __init__(self, bot, moduleName):
		" Module name is passed from the actual module "
		self.moduleName=moduleName
		" Reference to the bot is saved"
		self.bot = bot
		" Hooks are provided requested by the actual module "
		self.hooks=[]
		" Services provided by the actual module "
		self.services=[]
		" Config is blank until the Module calls loadConfig "
		self.config={}
		" Set up logging for this module "
		self.log = logging.getLogger("Module.%s" % self.moduleName)
		self.log.info("Loaded module %s" % self.moduleName)
		
	
	def loadConfig(self):
		configPath = self.bot.getConfigPath(self.moduleName)
		
		if os.path.exists( configPath ):
			self.config = yaml.load(open(configPath, 'r'))
	
	def ondisable(self):
		pass
	
	def getConfigPath(self):
		return self.bot.getConfigPath(self.moduleName)
	
	def getFilePath(self, f=None):
		return self.bot.getDataPath(self.moduleName) + (f if f else '')
	
class ModuleHook:
	def __init__(self, hook, method):
		self.hook=hook
		self.method=method