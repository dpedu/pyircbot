RPC Usage
=========

By default ``pyircbot`` starts a JSON RPC that has some abilities to control 
the bot. A list of methods can be found in the :doc:`BotRPC </api/rpc>` class.

The RPC interface can be used interactively:

.. code-block:: bash

   $ python3 -i -m pyircbot.rpcclient 127.0.0.1 1876
   Connecting to rpc....
   Connected to rpc
   Loaded modules: ['NickUser', 'LinkTitler', 'SQLite', 'RandQuote', 'AttributeStorageLite', 'Tell', 'Seen', 'Calc', 'Inventory', 'Urban', 'Services', 'PingResponder', 'Weather', 'Remind']
   >>>

Now, you have a python shell. An object named "rpc" is the JSON RPC client. A
basic command lets us get a list naming the currently loaded modules:

.. code-block:: python

   >>> modules = rpc.getLoadedModules()
   >>> for m in modules:
   ...     print(m)
   ...
   NickUser
   LinkTitler
   SQLite
   RandQuote
   AttributeStorageLite
   Tell
   Seen
   Calc
   Inventory
   Urban
   Services
   PingResponder
   Weather
   Remind
   >>>

We can retrieve an arbitrary property from a module: 

.. code-block:: python

   >>> rpc.getPluginVar("Weather", "config")
   [True, {'apikey': 'deadbeefcafe', 'defaultUnit': 'f'}]
   >>>

Or run a method in a module, passing args:

.. code-block:: python

   >>> rpc.pluginCommand("Calc", "getRandomCalc", ["#jesusandhacking"])
   [True, {'definition': "Loyal, unlike its predecessor", 'word': 'rhobot2', 'by': 'xMopxShell'}]
   >>>

Careful, you can probably crash the bot by tweaking the wrong things. Only 
basic types can be passed over the RPC connection. Trying to access anything 
extra results in an error:

.. code-block:: python

   >>> rpc.getPluginVar("Calc", "sql")
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
     File "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/jsonrpc.py", line 970, in __call__
       return self.__req(self.__name, args, kwargs)
     File "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/jsonrpc.py", line 943, in __req
       resp = self.__data_serializer.loads_response( resp_str )
     File "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/jsonrpc.py", line 647, in loads_response
       raise RPCInternalError(error_data)
   pyircbot.jsonrpc.RPCInternalError: <RPCFault -32603: 'Internal error.' (None)>
   >>>

Adding an RPC "interface" to your module is automatic - the bot's RPC already 
has access to your module's internals via the methods in ``BotRPC``. However, 
as a convention, it is recommended to prefix methods intended to be called via 
rpc with ``rpc_``.

Since only basic types (like string, integer, dict, etc) can be passed over 
RPC, a well-written module should have helper rpc methods to express and 
manipulate the module's state using only these types.

Using the RPC client in python code is very easy. The above shows how to use 
RPC methods using python; rpc clients can be created as so:

.. code-block:: python

    #!/usr/bin/env python3
    from pyircbot.rpcclient import connect
    rpc = connect("127.0.0.1", 1876)
