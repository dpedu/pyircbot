***********
PubSub Mode
***********

The PubSubClient module provides a ZeroMQ-based PubSub remote control capability to pyircbot. Well, what if you could
also run pyircbot modules as a client of the pubsub bus? Look no further!

Obviously, the :py:class:`pyircbot.modules.PubSubClient.PubSubClient` module should be enabled. Take note of the `name`
parameter (which may be left at the default "default").

The so-called footless (as opposed to headless, as the bot's head is the IRC client connection) client needs only a
small set of bootstrap modules:

- PingResponder (:py:class:`pyircbot.modules.PingResponder.PingResponder`)
- Services (:py:class:`pyircbot.modules.Services.Services`)
- PubSubClient (:py:class:`pyircbot.modules.PubSubClient.PubSubClient`)

Launch the bot and let it connect to the msgbus server.

Next, create a config identical to that of a normal pyircbot, but with any modules desired enabled. Also, read the
`--help` text for the `pubsubbot` program. Launch the `pubsubbot` process:

.. code-block:: shell

    pubsubbot -c config-sub.json --name <name>

After connecting to the message bus, `pubsubbot` will be hosting any configured modules. It can be exited and restarted
any time without affecting the IRC client connection!

For a module to support running in this mode, it must use only methods described in the Module Developers Guide. Using
APIs outside of this - while not discouraged - will definitely break compatibility.
