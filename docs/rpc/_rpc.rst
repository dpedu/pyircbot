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

Run a method in a module, passing args:

.. code-block:: python

   >>> rpc.pluginCommand("Calc", "getRandomCalc", ["#jesusandhacking"])
   [True, {'definition': "Loyal, unlike its predecessor", 'word': 'rhobot2', 'by': 'xMopxShell'}]
   >>>

Or simply pass a string to eval() or exec() to do anything. In this case, 
retrieving a full stack trace of the bot, which is useful during module 
development:

.. code-block:: python

   >>> print( rpc.eval("self.bot.irc.trace()")[1] )
   
   *** STACKTRACE - START ***

   # ThreadID: 140289192748800
   File: "/usr/lib/python3.4/threading.py", line 888, in _bootstrap
     self._bootstrap_inner()
   File: "/usr/lib/python3.4/threading.py", line 920, in _bootstrap_inner
     self.run()
   File: "/usr/lib/python3.4/threading.py", line 1184, in run
     self.finished.wait(self.interval)
   File: "/usr/lib/python3.4/threading.py", line 552, in wait
     signaled = self._cond.wait(timeout)
   File: "/usr/lib/python3.4/threading.py", line 293, in wait
     gotit = waiter.acquire(True, timeout)

   # ThreadID: 140289297204992
   File: "/usr/lib/python3.4/threading.py", line 888, in _bootstrap
     self._bootstrap_inner()
   File: "/usr/lib/python3.4/threading.py", line 920, in _bootstrap_inner
     self.run()
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/rpc.py", line 51, in run
     self.server.serve()
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/jsonrpc.py", line 1110, in serve
     self.__transport.serve( self.handle, n )
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/jsonrpc.py", line 851, in serve
     result = handler(data)
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/jsonrpc.py", line 1086, in handle
     result = self.funcs[method]( *params )
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/rpc.py", line 167, in eval
     return (True, eval(code))
   File: "<string>", line 1, in <module>
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/irccore.py", line 288, in trace
     for filename, lineno, name, line in traceback.extract_stack(stack):

   # ThreadID: 140289333405504
   File: "/usr/local/bin/pyircbot", line 5, in <module>
     pkg_resources.run_script('pyircbot==4.0.0-r02', 'pyircbot')
   File: "/usr/lib/python3/dist-packages/pkg_resources.py", line 528, in run_script
     self.require(requires)[0].run_script(script_name, ns)
   File: "/usr/lib/python3/dist-packages/pkg_resources.py", line 1394, in run_script
     execfile(script_filename, namespace, namespace)
   File: "/usr/lib/python3/dist-packages/pkg_resources.py", line 55, in execfile
     exec(compile(open(fn).read(), fn, 'exec'), globs, locs)
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/EGG-INFO/scripts/pyircbot", line 32, in <module>
     bot.loop()
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/pyircbot.py", line 68, in loop
     self.irc.loop()
   File: "/usr/local/lib/python3.4/dist-packages/pyircbot-4.0.0_r02-py3.4.egg/pyircbot/irccore.py", line 56, in loop
     asyncore.loop(map=self.asynmap)
   File: "/usr/lib/python3.4/asyncore.py", line 208, in loop
     poll_fun(timeout, map)
   File: "/usr/lib/python3.4/asyncore.py", line 145, in poll
     r, w, e = select.select(r, w, e, timeout)

   *** STACKTRACE - END ***
   
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
an existing RPC client using python; rpc clients can be created as so:

.. code-block:: python

    #!/usr/bin/env python3
    from pyircbot.rpcclient import connect
    rpc = connect("127.0.0.1", 1876)
