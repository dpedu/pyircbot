*********************
Initial Configuration
*********************

This is a quick-start guide for the minimal setup to run PyIRCBot.

Getting Started
===============

PyIRCBot is modular. The core bot files will reside whereever your system keeps
python modules. User modules and data are kept where you want. This way, setups
can be created where many unprivileged users may rely one one set of
core/module files they cannot edit, but can customize their instance.

Configuration is stored in 2 locations:

- **Instance config** - Information about one instance of the bot, such as
  where module data for the instance will be stored, server address, etc.
- **Module config** - Where module configuration settings are be stored

Instance Configuration
======================

.. code-block:: json

    {
        "bot":{
            "datadir":"./data/",
            "rpcbind":"0.0.0.0",
            "rpcport":1876,
            "usermodules": [ "./data/modules/" ]
        },
        "connection":{
            "servers": [
                ["weber.freenode.net", 6667],
                ["asimov.freenode.net", 6667],
                ["card.freenode.net", 6667],
                ["dickson.freenode.net", 6667],
                ["morgan.freenode.net", 6667]
            ],
            "force_ipv6": false,
            "force_ipv4": false,
            "bind": ["1.2.3.4", 5678]
        },
        "modules":[
            "PingResponder",
            "Services"
        ]
    }

In the example directory, this is stored in `config.json`. This may be
substituted for a YML file with the same data structure. This contains several
options:

.. cmdoption:: bot.datadir

    Location where module data will be stored. This directory must contains
    two directories: `config` and `data`. Config contains a config file for
    each module of the same name (for example: Services.json for ``Services``
    module). Data can be empty, the bot will create directories for each
    module as needed.

.. cmdoption:: bot.rpcbind

    Address on which to listen for RPC conncetions. RPC has no authentication
    so using 127.0.0.1 is reccommended.

.. cmdoption:: bot.rpcport

    Port on which RPC will listen

.. cmdoption:: bot.usermodules

    Paths to directories where modules where also be included from

.. cmdoption:: connection.servers

    List of hostnames or IP addresses and ports of the IRC server to connection
    to. First entry will be used for the initial connection on startup. If we
    the bot must reconnect to the IRC server later, the next server will
    be used.

.. cmdoption:: connection.force_ipv6

    Enable this option to force use of ipv6 connections and ignore ipv4 server addresses.

.. cmdoption:: connection.force_ipv4

    Enable this option to force use of ipv4 connections and ignore ipv6 server addresses. Enabling force_ipv6
    overrides force_ipv4.

.. cmdoption:: connection.bind

    Set the local address and port to bind the connection to.

.. note::

    To bind to an address but no specific port, set the second tuple entry to `null`.

.. cmdoption:: modules

    A list of modules to load. Modules are loaded in the order they are listed
    here. :doc:`PingResponder </api/modules/pingresponder>` and :doc:`Services </api/modules/services>` are the *bare minimum* needed to open and
    maintain and IRC connection.
