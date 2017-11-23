#!/usr/bin/env python3

"""
.. module::ModInfo
    :synopsis: Provides manpage-like info for commands
"""


from pyircbot.modulebase import ModuleBase, command


class info(object):
    """
    Decorator for tagging module methods with help text

    .. code-block:: python
        from pyircbot.modules.ModInfo import info

        ...

        @info("help [command]    show the manual for all or [commands]", cmds=["help", "rtfm"])
        @command("help")
        def cmd_help(self, msg, cmd):
            ...

    :param docstring: command help formatted as above
    :type docstring: str
    :param cmds: enable command names or aliases this function implements, as a list of strings. E.g. if the "help"
    command has the alias "rtfm"
    :type cmds: list
    """
    def __init__(self, docstring, cmds=None):
        self.docstring = docstring
        self.commands = cmds or []

    def __call__(self, func):
        setattr(func, "irchelp", self.docstring)
        setattr(func, "irchelpc", self.commands)
        return func


class ModInfo(ModuleBase):

    @info("help [command]    show the manual for all or [commands]", cmds=["help"])
    @command("help")
    def cmd_help(self, msg, cmd):
        """
        Get help on a command
        """
        if cmd.args:
            for modname, module, helptext, helpcommands in self.iter_modules():
                if cmd.args[0] in ["{}{}".format(command.prefix, i) for i in helpcommands]:
                    self.bot.act_PRIVMSG(msg.args[0], "RTFM: {}: {}".format(cmd.args[0], helptext))
        else:
            for modname, module, helptext, helpcommands in self.iter_modules():
                self.bot.act_PRIVMSG(msg.args[0], "{}: {}{}".format(modname, command.prefix, helptext))

    @command("helpindex")
    def cmd_helpindex(self, msg, cmd):
        """
        Short index of commands
        """
        commands = []
        for modname, module, helptext, helpcommands in self.iter_modules():
            commands += ["{}{}".format(command.prefix, i) for i in helpcommands]

        self.bot.act_PRIVMSG(msg.args[0], "{}: commands: {}".format(msg.prefix.nick, ", ".join(commands)))

    def iter_modules(self):
        """
        Iterator that cycles through module methods that are tagged with help information. The iterator yields tuples
        of:

        (module_name, module_object, helptext, command_list)
        """
        for modname, module in self.bot.moduleInstances.items():
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, "irchelp"):
                    yield (modname, module, getattr(attr, "irchelp"), getattr(attr, "irchelpc"), )
        raise StopIteration()
