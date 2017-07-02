"""
.. module:: ModuleBase
    :synopsis: Base class that modules will extend

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import logging
from .pyircbot import PyIRCBot
from inspect import getargspec
import os


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

        self.irchooks = []
        """IRC Hooks this module has"""

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
            if not callable(attr):
                continue
            if hasattr(attr, ATTR_ACTION_HOOK):
                for action in getattr(attr, ATTR_ACTION_HOOK):
                    self.hooks.append(ModuleHook(action, attr))
            if hasattr(attr, ATTR_COMMAND_HOOK):
                for action in getattr(attr, ATTR_COMMAND_HOOK):
                    self.irchooks.append(IRCHook(action, attr))

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
        return os.path.join(self.bot.getDataPath(self.moduleName), (f if f else ''))


class ModuleHook:
    def __init__(self, hook, method):
        self.hook = hook
        self.method = method


class IRCHook:
    def __init__(self, hook, method):
        self.hook = hook
        self.method = method

    def call(self, msg):
        self.hook.call(self.method, msg)


ATTR_ACTION_HOOK = "__tag_hooks"
ATTR_COMMAND_HOOK = "__tag_commands"


class hook(object):
    """
    Decorator for calling module methods in response to IRC actions. Example:

    .. code-block:: python

        @hook("PRIVMSG")
        def mymyethod(self, message):
            print("IRC server sent PRIVMSG")

    This stores a list of IRC actions each function is tagged for in method.__tag_hooks. This attribute is scanned
    during module init and appropriate hooks are set up.

    :param args: irc protocol event to listen for. See :py:meth:`pyircbot.irccore.IRCCore.initHooks` for a complete list
    :type args: str
    """
    def __init__(self, *args):
        self.commands = args

    def __call__(self, func):
        if not hasattr(func, ATTR_ACTION_HOOK):
            setattr(func, ATTR_ACTION_HOOK, list(self.commands))
        else:
            getattr(func, ATTR_ACTION_HOOK).extend(self.commands)
        return func


class irchook(object):
    def __call__(self, func):
        if not hasattr(func, ATTR_COMMAND_HOOK):
            setattr(func, ATTR_COMMAND_HOOK, [self])
        else:
            getattr(func, ATTR_COMMAND_HOOK).extend(self)
        return func

    def validate(self, msg, bot):
        """
        Return True if the message should be passed on. False otherwise.
        """
        return True


class command(irchook):
    """
    Decorator for calling module methods when a command is parsed from chat

    .. code-block:: python

        @command("ascii")
        def cmd_ascii(self, cmd, msg):
            print("Somebody typed .ascii with params {} in channel {}".format(str(cmd.args), msg.args[0]))

    This stores a list of IRC actions each function is tagged for in method.__tag_commands. This attribute is scanned
    during module init and appropriate hooks are set up.

    :param keywords: commands to listen for
    :type keywords: str
    :param require_args: only match if trailing data is passed with the command used
    :type require_args: bool
    :param allow_private: enable matching in private messages
    :type allow_private: bool
    """

    prefix = "."
    """
    Hotkey that must appear before commands
    """

    def __init__(self, *keywords, require_args=False, allow_private=False):
        self.keywords = keywords
        self.require_args = require_args
        self.allow_private = allow_private
        self.parsed_cmd = None

    def call(self, method, msg):
        """
        Internal use. Triggers the hooked function
        """
        if len(getargspec(method).args) == 3:
            return method(self.parsed_cmd, msg)
        else:
            return method(self.parsed_cmd)

    def validate(self, msg, bot):
        """
        Test a message and return true if matched.

        :param msg: message to test against
        :type msg: pyircbot.irccore.IRCEvent
        :param bot: reference to main pyircbot
        :type bot: pyircbot.pyircbot.PyIRCBot
        """
        if not self.allow_private and msg.args[0] == "#":
            return False
        for keyword in self.keywords:
            if self._validate_one(msg, keyword):
                return True
        return False

    def _validate_one(self, msg, keyword):
        with_prefix = "{}{}".format(self.prefix, keyword)
        cmd = PyIRCBot.messageHasCommand(with_prefix, msg.trailing, requireArgs=self.require_args)
        if cmd:
            self.parsed_cmd = cmd
            return True
        return False
