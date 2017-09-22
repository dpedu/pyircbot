:mod:`PubSubClient` --- Message bus based RPC
=============================================


This module connects to a pub/sub message bus and provices RPC functionality.
It broadcasts status messages and reacts to different messages. The client /
server for the message bus is http://gitlab.davepedu.com/dave/pymsgbus. Under
the hood, this is ZeroMQ.

Config
------

.. code-block:: json

    {
        "servers": ["127.0.0.1:7100"],
        "subscriptions": ["pyircbot_send"],
        "publish": "pyircbot_{}",
        "name": "default"
    }

.. cmdoption:: servers

    Message bus server(s) to connect or fall back to. Currently, only use of
    the first is implemented.

.. cmdoption:: subscriptions

    List of bus channels to subscribe to

.. cmdoption:: publish

    Publish channel name template. Will be formatted with the sub-type of
    message, such as `privmsg`.

.. cmdoption:: name

    Multiple bots can connect to one bus. They can be given a name to target a
    single bot; all will respond to the `default` name.

Bus Messages
------------

In the format of:

.. code-block:: text

    <channel name> <message body>

Bot connects to the bus:

.. code-block:: text

    pyircbot_sys default online

Bot disconnects from the bus:

.. code-block:: text

    pyircbot_sys default offline

Bot relaying a privmsg:

.. code-block:: text

    pyircbot_privmsg default [["#clonebot"], "dave-irccloud", "message text",
                              {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

User parts a channel:

.. code-block:: text

    pyircbot_part default [["#clonebot"], "dave-irccloud", "part msg",
                           {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

User joins a channel:

.. code-block:: text

    pyircbot_join default ["dave-irccloud", "#clonebot",
                           {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

User uses the command `.seen testbot`:

.. code-block:: text

    pyircbot_command_seen default [["#clonebot"], "dave-irccloud", "testbot",
                                   {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

Client sending a message that the bot will relay

.. code-block:: text

    pyircbot_send default privmsg ["#clonebot", "asdf1234"]

"""

Example Programs
----------------

Sends the content of a text file line-by-line with a delay:

.. code-block:: python

    from contextlib import closing
    from msgbus.client import MsgbusSubClient
    import argparse
    from time import sleep
    from json import dumps


    def main():
        parser = argparse.ArgumentParser(description="send irc art")
        parser.add_argument("-i", "--host", default="127.0.0.1", help="host to connect to")
        parser.add_argument("-p", "--port", default=7003, help="port to connect to")
        parser.add_argument("-c", "--channel", required=True, help="irc channel")
        parser.add_argument("-f", "--file", required=True, help="file containing irc lines to send")
        parser.add_argument("--delay", type=float, default=1.0, help="delay between lines (s)")
        args = parser.parse_args()

        with open(args.file) as f:
            with closing(MsgbusSubClient(args.host, args.port)) as client:
                for line in f:
                    line = line.rstrip()
                    print(line)
                    client.pub("pyircbot_send", "default privmsg {}".format(dumps([args.channel, line])))
                    sleep(args.delay)


    if __name__ == '__main__':
        main()

Class Reference
---------------

.. automodule:: pyircbot.modules.PubSubClient
    :members:
    :undoc-members:
    :show-inheritance:
