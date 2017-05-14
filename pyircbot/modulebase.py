"""
.. module:: ModuleBase
    :synopsis: Base class that modules will extend

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import logging
from .pyircbot import PyIRCBot


class ModuleBase:
    """All modules will extend this class

    :param bot: A reference to the main bot passed when this module is created
    :type bot: PyIRCBot
    :param moduleName: The name assigned to this module
    :type moduleName: str
    """

    def __init__(self, bot, moduleName):
        self.moduleName = moduleName
        """Assigned name of this module"""

        self.bot = bot
        """Reference to the master PyIRCBot object"""

        self.hooks = []
        """Hooks (aka listeners) this module has"""

        self.services = []
        """If this module provides services usable by another module, they're listed
        here"""

        self.config = {}
        """Configuration dictionary. Autoloaded from `%(datadir)s/%(modulename)s.json`"""

        self.log = logging.getLogger("Module.%s" % self.moduleName)
        """Logger object for this module"""

        # Autoload config if available
        self.loadConfig()

        # Prepare any function hooking
        self.init_hooks()

        self.log.info("Loaded module %s" % self.moduleName)

    def init_hooks(self):
        """
        Scan the module for tagged methods and set up appropriate protocol hooks.
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, ATTR_ACTION_HOOK):
                for action in getattr(attr, ATTR_ACTION_HOOK):
                    self.hooks.append(ModuleHook(action, attr))

    def loadConfig(self):
        """
        Loads this module's config into self.config. The bot's main config is checked for a section matching the module
        name, which will be preferred. If not found, an individual config file will be loaded from the data dir
        """
        self.config = self.bot.botconfig.get("module_configs", {}).get(self.__class__.__name__, {})
        if not self.config:
            configPath = self.getConfigPath()
            if configPath is not None:
                self.config = PyIRCBot.load(configPath)

    def ondisable(self):
        """Called when the module should be disabled. Your module should do any sort
        of clean-up operations here like ending child threads or saving data files.
        """
        pass

    def getConfigPath(self):
        """Returns the absolute path of this module's json config file"""
        return self.bot.getConfigPath(self.moduleName)

    def getFilePath(self, f=None):
        """Returns the absolute path to a file in this Module's data dir

        :param f: The file name included in the path
        :type channel: str
        :Warning: .. Warning::  this does no error checking if the file exists or is\
            writable. The bot's data dir *should* always be writable"""
        return self.bot.getDataPath(self.moduleName) + (f if f else '')


class ModuleHook:
    def __init__(self, hook, method):
        self.hook = hook
        self.method = method


ATTR_ACTION_HOOK = "__tag_hooks"


class hook(object):
    """
    Decorating for calling module methods in response to IRC actions. Example:
    ```
    @hook("PRIVMSG")
    def mymyethod(self, message):
        print("IRC server sent PRIVMSG")
    ```
    This stores a list of IRC actions each function is tagged for in method.__tag_hooks. This attribute is scanned
    during module init and appropriate hooks are set up.
    """
    def __init__(self, *args):
        self.commands = args

    def __call__(self, func):
        """

        """
        if not hasattr(func, ATTR_ACTION_HOOK):
            setattr(func, ATTR_ACTION_HOOK, list(self.commands))
        else:
            getattr(func, ATTR_ACTION_HOOK).extend(self.commands)
        return func
