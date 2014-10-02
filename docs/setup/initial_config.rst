*********************
Initial Configuration
*********************

This is a quick-start guide for the minimal setup to run PyIRCBot.

Getting Started
===============

PyIRCBot is modular. The core bot files may reside in one directory, modules in
another, and userdata in a third. This way, setups can be created where many
unprivileged users may rely one one set of core/module files they cannot edit,
but can customize their instance.

Configuration is stored in 3 locations:

- **Core config** - Environmental information for the bot, like where modules and 
  core code is.
- **Instance config** - Information about one instance of the bot, such as where
  module data for the instance will be stored, server address, etc
- **Module config** - Where module configuration files will be stored

Core Configuration
==================

.. code-block:: python
    
    botdir: /home/example/bot/pyircbot/
    moduledir: /home/example/bot/pyircbot/modules/

The example core configuration is stored in `config.main.yml`. This contains two options:

.. cmdoption:: botdir

    Must be the absolute path to where main.py and the directory `core` resides.

.. cmdoption:: moduledir

    must be the absolute path to the directory of modules is.

.. note:: All paths require a trailing slash

Instance Configuration
======================

.. code-block:: yaml

    bot:
      datadir: /home/example/bot/data/
      rpcbind: 0.0.0.0
      rpcport: 1876
    connection:
      server: irc.freenode.net
      ipv6: off
      port: 6667
    modules:
      - PingResponder
      - Services
      - MySQL
      - AttributeStorage

The example bot instance is stored in `config.instance.yml`. This contains several options:

.. cmdoption:: bot.datadir

    Location where module data will be stored. This directory generally contains
    two folders: `config` and `data`. Config contains a yml file for each module
    of the same name. Data can be empty, the bot will create directories for
    each module as needed.

.. cmdoption:: bot.rpcbind

    Address on which to listen for RPC conncetions. RPC has no authentication so
    using 127.0.0.1 is reccommended.

.. cmdoption:: bot.rpcport

    Port on which RPC will listen

.. cmdoption:: connection.server

    Hostname or IP of the IRC server to connection to

.. cmdoption:: connection.ipv6

    Enable or disable defaulting to IPv6 using the value "off" or "on"

.. cmdoption:: connection.port

    Port to connect to on the IRC server

.. cmdoption:: modules

    A YAML list of modules to load. Modules are loaded in the order they are listed here.