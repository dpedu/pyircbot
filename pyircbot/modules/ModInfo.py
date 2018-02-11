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
    def __init__(self, cmdspec, docstring, cmds=None):
        self.cmdspec = cmdspec
        self.docstring = docstring
        self.aliases = cmds or []

    def __call__(self, func):
        if hasattr(func, "irchelp"):
            func.irchelp.append(self)
        else:
            setattr(func, "irchelp", [self])
        return func


class ModInfo(ModuleBase):

    @info("help [command]", "show the manual for all or [commands]", cmds=["help"])
    @command("help")
    def cmd_help(self, msg, cmd):
        """
        Get help on a command
        """
        if cmd.args:
            for modname, module, cmdspec, docstring, aliases in self.iter_modules():
                if cmd.args[0] in ["{}{}".format(command.prefix, i) for i in aliases]:
                    self.bot.act_PRIVMSG(msg.args[0], "RTFM: {}: ({}{}) {}"
                                         .format(cmd.args[0], command.prefix, cmdspec, docstring))
        else:
            rows = []
            for modname, module, cmdspec, docstring, aliases in self.iter_modules():
                rows.append((modname, command.prefix + cmdspec, docstring))
            rows.sort(key=lambda item: item[0] + item[1])
            self.send_columnized(msg.args[0], rows)

    def send_columnized(self, channel, rows):
        if not rows:
            return
        widths = []
        # Find how many col widths we must calculate
        for _ in rows[0]:
            widths.append(0)
        # Find widest value per col
        for row in rows:
            for col, value in enumerate(row):
                print(col, value)
                vlen = len(value)
                if vlen > widths[col]:
                    widths[col] = vlen
        # Print each row
        for row in rows:
            message = ""
            for colid, col in enumerate(row):
                message += str(col)
                message += (" " * (widths[colid] - len(col) + 1))
            self.bot.act_PRIVMSG(channel, message)

    @info("helpindex", "show a short list of all commands", cmds=["helpindex"])
    @command("helpindex")
    def cmd_helpindex(self, msg, cmd):
        """
        Short index of commands
        """
        commands = []
        for modname, module, cmdspec, docstring, aliases in self.iter_modules():
            commands += ["{}{}".format(command.prefix, i) for i in aliases]

        self.bot.act_PRIVMSG(msg.args[0], "{}: commands: {}".format(msg.prefix.nick, ", ".join(commands)))

    def iter_modules(self):
        """
        Iterator that cycles through module methods that are tagged with help information. The iterator yields tuples
        of:

        (module_name, module_object, command_spec, command_help, command_list)
        """
        for modname, module in self.bot.moduleInstances.items():
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, "irchelp"):
                    for cmdinfo in attr.irchelp:
                        yield (modname, module, cmdinfo.cmdspec, cmdinfo.docstring, cmdinfo.aliases)
        raise StopIteration()
