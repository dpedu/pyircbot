:mod:`ModInfo` --- Module command help system
=============================================

Implements global `help` and `helpindex` commands that print help information about all available modules. Modules must
import and use a decorator from this module. For example:


.. code-block:: python

    from pyircbot.modules.ModInfo import info

    # ...

    @info("help [command]", "show the manual for all or [commands]", cmds=["help"])
    @command("help")
    def cmd_help(self, msg, cmd):
        # ...


The `info` decorator takes mandatory string parameters describing the command. The first is an argspec; simply the name
of the command with parameters marked using `<` and `>`. Optional parameters should be encased in `[`square brackets`]`.
The second parameter is a short text description of the command. The third, optional, list parameter `cmds` is a list of
short names thart are aliases for the function that aide in help lookup. In all cases, the cases, commands will be
prefixed with the default command prefix (`from pyircbot.modulebase.command.prefix`).


Class Reference
---------------

.. automodule:: pyircbot.modules.ModInfo
    :members:
    :undoc-members:
    :show-inheritance:
