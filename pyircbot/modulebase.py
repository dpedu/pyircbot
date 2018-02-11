"""
.. module:: ModuleBase
    :synopsis: Base class that modules will extend

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import re
import os
import logging
from .common import load as pload
from .common import messageHasCommand


class ModuleBase(object):
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
            if hasattr(attr, ATTR_ALL_HOOKS):
                for hook in getattr(attr, ATTR_ALL_HOOKS):
                    self.irchooks.append(IRCHook(hook.validate, attr))

    def loadConfig(self):
        """
        Loads this module's config into self.config. The bot's main config is checked for a section matching the module
        name, which will be preferred. If not found, an individual config file will be loaded from the data dir
        """
        self.config = self.bot.botconfig.get("module_configs", {}).get(self.__class__.__name__, {})
        if not self.config:
            configPath = self.getConfigPath()
            if configPath is not None:
                self.config = pload(configPath)

    def onenable(self):
        """Called when the module is enabled"""
        pass

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
    def __init__(self, validator, method):
        """
        :param validator: method accpeting an IRCEvent and returning false-like or true-like depending on match
        :param method: module method
        """
        self.validator = validator
        self.method = method


ATTR_ALL_HOOKS = "__hooks"


class AbstractHook(object):
    """
    Decorator for calling module methods in response to arbitrary IRC actions. Example:

    .. code-block:: python

        @myhooksubclass(<conditions>)
        def mymyethod(self, message, extra):
            print("IRC server sent something that matched <conditions>")

    This stores some record of the above filtering in an attribute of the decorated method, such as method.__tag_hooks.
    This attribute is scanned during module init and appropriate hooks are set up.

    Hooks implement a validate() method that return a true-like or false-like item, dictating whether the hooked method
    will be called (with the message and true-like object as parameters)

    :param args: irc protocol event to listen for. See :py:meth:`pyircbot.irccore.IRCCore.initHooks` for a complete list
    :type args: str
    """
    def __init__(self):
        # todo do i need this here for the docstring?
        pass

    def __call__(self, func):
        """
        Store a list of such hooks in an attribute of the decorated method
        """
        if not hasattr(func, ATTR_ALL_HOOKS):
            setattr(func, ATTR_ALL_HOOKS, [self])
        else:
            getattr(func, ATTR_ALL_HOOKS).extend(self)
        return func

    def validate(self, msg, bot):
        """
        Return a true-like item if the hook matched. Otherwise, false.
        :param msg: IRCEvent instance of the message
        :param bot: reference to the bot TODO remove this
        """
        return True


class hook(AbstractHook):
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

    def validate(self, msg, bot):
        if msg.command in self.commands:
            return True


class command(hook):
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
    :param require_args: only match if trailing data is passed with the command used. False-like values disable This
        requirement. True-like values require any number of args greater than one. Int values require a specific
        number of args
    :type require_args: bool, int
    :param allow_private: enable matching in private messages
    :type allow_private: bool
    :param allow_highlight: treat 'Nick[:,] command args' the same as '.command args'
    """

    prefix = "."
    """
    Hotkey that must appear before commands
    """

    def __init__(self, *keywords, require_args=False, allow_private=False, allow_highlight=True):
        super().__init__("PRIVMSG")
        self.keywords = keywords
        self.require_args = require_args
        self.allow_private = allow_private
        self.allow_highlight = allow_highlight

    def validate(self, msg, bot):
        """
        Test a message and return true if matched.

        :param msg: message to test against
        :type msg: pyircbot.irccore.IRCEvent
        :param bot: reference to main pyircbot
        :type bot: pyircbot.pyircbot.PyIRCBot
        """
        bot_nick = bot.get_nick()
        if not super().validate(msg, bot):
            return False
        if msg.args[0][0] != "#" and not self.allow_private:
            return False
        for keyword in self.keywords:
            single = self._validate_prefixedcommand(msg, keyword, bot_nick)
            if single:
                print(single)
                return single
        return False

    def _validate_prefixedcommand(self, msg, keyword, nick):
        with_prefix = "{}{}".format(self.prefix, keyword)
        return messageHasCommand(with_prefix, msg.trailing,
                                 requireArgs=self.require_args,
                                 withHighlight=nick if self.allow_highlight else False)


class regex(hook):
    """
    Decorator for calling module methods when a message matches a regex.

    .. code-block:: python

        @regex(r'^foobar$')
        def cmd_foobar(self, matches, msg):
            print("Someone's message was exactly "foobar" ({}) in channel {}".format(msg.message, msg.args[0]))

    :param regexps: expressions to match for
    :type keywords: str
    :param allow_private: enable matching in private messages
    :type allow_private: bool
    :param types: list of irc commands such as PRIVMSG to accept
    :type types: list
    """

    def __init__(self, *regexps, allow_private=False, types=None):
        super().__init__("PRIVMSG")
        self.regexps = [re.compile(r) for r in regexps]
        self.allow_private = allow_private
        self.types = types

    def validate(self, msg, bot):
        """
        Test a message and return true if matched.

        :param msg: message to test against
        :type msg: pyircbot.irccore.IRCEvent
        :param bot: reference to main pyircbot
        :type bot: pyircbot.pyircbot.PyIRCBot
        """
        if not super().validate(msg, bot):
            return False
        if self.types and msg.command not in self.types:
            return False
        if not self.allow_private and msg.args[0] == "#":
            return False
        for exp in self.regexps:
            matches = exp.search(msg.trailing)
            if matches:
                return matches
        return False


class MissingDependancyException(Exception):
    """
    Exception expressing that a pyricbot module could not find a required module
    """
