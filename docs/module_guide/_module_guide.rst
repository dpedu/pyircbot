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

    from pyircbot.modulebase import ModuleBase,ModuleHook
    class EchoExample(ModuleBase):

The class's ``__init__`` method accepts 2 args - a reference to the bot's API
and what the bot has decided to name this module. These are passed to
ModuleBase. Module's init method should be as quick as possible. The bot loads 
modules one after the other so a long delay slows bot startup.

.. code-block:: python

        def __init__(self, bot, moduleName):
            ModuleBase.__init__(self, bot, moduleName);

If your module has a config file - EchoExample.json - it can be loaded by 
calling :py:meth:`pyircbot.modulebase.ModuleBase.loadConfig`:

.. code-block:: python

            self.loadConfig()
            print(self.config)

In ``__init__``, the module lists what hooks it wants to listen for. Hooks are
executed when the corresponding IRC protocol command is received. 

.. code-block:: python

            self.hooks=[ModuleHook("PRIVMSG", self.echo)]

Then, a handler for this hook:

.. code-block:: python

        def echo(self, args, prefix, trailing):

The handler is passed the data sent by the irc server. What these are can vary,
but the format is the same. ``args`` is the list of arguments the IRC server
sent. ``prefix`` is the sender. ``trailing`` is arbitrary data associated with 
the event. In the case of PRIVMSG: args has one entry - the channel name or 
nick the message was in/from. Prefix is a user's nick string, in the format of:
NickName!username@ip. Trailing is message content. Since the module describe 
above echos messages, let's do that:

.. code-block:: python

            self.bot.act_PRIVMSG(args[0], trailing)

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

Advanced Usage
==============

Check out the helper methods that :doc:`ModuleBase </api/modulebase>` offers.

Refer to existing modules for helper methods from elsewhere in PyIRCBot.

:doc:`PyIRCBot </api/pyircbot>` has some useful methods:

- :py:meth:`pyircbot.pyircbot.PyIRCBot.messageHasCommand`
- :py:meth:`pyircbot.pyircbot.PyIRCBot.getDataPath`
- :py:meth:`pyircbot.pyircbot.PyIRCBot.getmodulebyname`


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
            ModuleBase.__init__(self, bot, moduleName);
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
