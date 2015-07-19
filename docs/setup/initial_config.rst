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
            "rpcport":1876
        },
        "connection":{
            "server":"irc.freenode.net",
            "ipv6":"off",
            "port":6667
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

.. cmdoption:: connection.server

    Hostname or IP of the IRC server to connection to

.. cmdoption:: connection.ipv6

    Enable or disable defaulting to IPv6 using the value "off" or "on"

.. cmdoption:: connection.port

    Port to connect to on the IRC server

.. cmdoption:: modules

    A list of modules to load. Modules are loaded in the order they are listed
    here. :doc:`PingResponder </api/modules/pingresponder>` and :doc:`Services </api/modules/services>` are the *bare minimum* needed to open and
    maintain and IRC connection.
