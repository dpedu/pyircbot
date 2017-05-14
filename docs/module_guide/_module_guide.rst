************************
Module Developer's Guide
************************

Modules consist of a single python file, named for the module. For example, EchoExample.py

Getting Started
===============

All modules should inherit from the base class
:doc:`ModuleBase </api/modulebase>`, and should be named matching their python
file's name.

.. code-block:: python

    from pyircbot.modulebase import ModuleBase, hook
    class EchoExample(ModuleBase):

The class's ``__init__`` method accepts 2 args - a reference to the bot's API
and what the bot has decided to name this module. These are passed to
ModuleBase. Module's init method should be as quick as possible. The bot loads
modules sequentially on startup and you should avoid long operations here as it
will undesirably slow bot startup time.

.. code-block:: python

        def __init__(self, bot, moduleName):
            ModuleBase.__init__(self, bot, moduleName)

If your module has a config file - EchoExample.json - it will be automatically
loaded on module startup. It can be manually reloaded by
calling :py:meth:`pyircbot.modulebase.ModuleBase.loadConfig`:

.. code-block:: python

            print(self.config)
            self.loadConfig()  # Manually reload config

Any other setup code should be placed in ``__init__``. Note that ``__init__``
will be executed when the bot is starting up and before the irc connection is
opened.

Adding interaction
------------------

In order to make your module respond to various IRC commands, pyircbot uses a
system of "hooks", which can be defined using decorators or programmatically.
Note: in this case, "commands" refers to IRC protocol commands such as PRIVMSG,
KICK, JOIN, etc. Pyircbot also provides some meta-events that are accessed in
the same way. The complete list of supported commands can be seen in the source
of :py:meth:`pyircbot.irccore.IRCCore.initHooks`.

The easiest method is to use the ``hook`` decorator on any function your want
called when an IRC command is received.

.. code-block:: python

        @hook("PRIVMSG")
        def echo(self, event):

The handler is passed and IRCEvent object containing the data sent by the irc
server. The values of these are can vary, but the format is alwaysthe same.

``event.args`` is the list of arguments the IRC server sent. ``event.prefix``
is the sender, parsed. ``trailing`` is arbitrary data associated
with the event. In the case of PRIVMSG: args has one entry - the channel name
or  nick the message was in/from.

Prefix is an ``UserPrefix`` object with the properties ``event.prefix.nick``,
``event.prefix.username``, ``event.prefix.hostname``, and the original unparsed
prefix, ``event.prefix.str``.

Prefix may also be a ``ServerPrefix`` object, if the hook is for an IRC method
that interacts with the server directly, such as PING. It would have the
properties ``event.prefix.hostname`` and ``event.prefix.str``.

Since the module described above echos messages, let's do that:

.. code-block:: python

            self.bot.act_PRIVMSG(event.args[0], event.trailing)

This sends a PRIVMSG to the originating channel or nick, with the same msg
content that was received.

Beyond this, a module's class can import or do anything python can to deliver
responses. For modules that use threads or connect to external services, a
shutdown handler is needed to ensure a clean shutdown.

.. code-block:: python

        def ondisable(self):
            """Called when the module should be disabled. Your module should do any sort
            of clean-up operations here like ending child threads or saving data files.
            """
            pass

EchoExample module
------------------

This is the snippets above combined into a usable module.

.. code-block:: python

    from pyircbot.modulebase import ModuleBase, hook

    class EchoExample(ModuleBase):
        def __init__(self, bot, moduleName):
            ModuleBase.__init__(self, bot, moduleName)
            print(self.config)

        @hook("PRIVMSG")
        def echo(self, event):
            self.bot.act_PRIVMSG(event.args[0], event.trailing)

        def ondisable(self):
            print("I'm getting unloaded!")

In usage:

.. code-block:: text

    4:40:17 PM <Beefpile> test
    4:40:17 PM <derpbot420> test

New Style Module Hooks
----------------------

Instead of receiving the values of the IRC event a module is responding to in
3 separate arguments, hooks can receive them as one object. The hook system
will automatically determine which argument style to use.

The reason for this change is to eliminate some unnecessary code in modules.
Any module that looks at a user's nick or hostname may find itself doing
something like this in every hook:

.. code-block:: python

        def saynick(self, args, prefix, trailing):
            prefixObj = self.bot.decodePrefix(prefix)
            self.bot.act_PRIVMSG(args[0], "Hello, %s. You are connecting from %s" % (prefixObj.nick, prefixObj.hostname))

With the new style, one line can be eliminated, as the passed ``IRCEvent``
event has the prefix already parsed:

.. code-block:: python

        def saynick(self, event):
            self.bot.act_PRIVMSG(event.args[0], "Hello, %s. You are connecting from %s" % (event.prefix.nick, event.prefix.hostname))

Advanced Usage
==============

Check out the helper methods that :doc:`ModuleBase </api/modulebase>` offers.

Refer to existing modules for helper methods from elsewhere in PyIRCBot.

:doc:`PyIRCBot </api/pyircbot>` has some useful methods:

- :py:meth:`pyircbot.pyircbot.PyIRCBot.messageHasCommand`
- :py:meth:`pyircbot.pyircbot.PyIRCBot.getDataPath`
- :py:meth:`pyircbot.pyircbot.PyIRCBot.getmodulebyname`

:doc:`GameBase </api/modules/gamebase>` is a good example of the basic code
structure a IRC game could follow, designed so different channels would have
separate game instances.

Inter-module Communication
--------------------------

In the list above, :py:meth:`pyircbot.pyircbot.PyIRCBot.getmodulebyname` can be
used to retrieve a reference to another loaded module. This is simply the
instance of the other module's class.

But what if you wanted a module to find another by type? For example, a module
providing a cache API could provide a service called "cache". Modules that use
a cache API to function could find this module - or another that's functionally
equivalent.

Modules providing a service state so like:

.. code-block:: python

        def __init__(self, bot, moduleName):
            ModuleBase.__init__(self, bot, moduleName)
            self.services=["cache"]

Then, another module can find this one by using either
:py:meth:`pyircbot.pyircbot.PyIRCBot.getmodulesbyservice` or
:py:meth:`pyircbot.pyircbot.PyIRCBot.getBestModuleForService` and passing the
name "cache". The first returns a list of all modules offering the "cache"
service, the second returns an arbitrary module returning cache if more that
one is found.

**PyIRCBot does NOT automatically handle inter-module communication. Meaning,
modules providing a service should be loaded before modules requiring the
service. Modules using a service MUST BE unloaded before the service module
is unloaded.**
