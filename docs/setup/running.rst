*************
Running a bot
*************

It is reccommended to install PyIRCBot3 with Pip or by running the install
script included in the module folder. This installs the `pyircbot` command into
 your $PATH, which is the easiest way to launch a bot. This document assumes it
has been installed this way. 


The bot is invoked from the command line:

.. code-block:: sh

    pyircbot --config config.json

.. cmdoption:: -c --config

    Path to the bot's :doc:`config </setup/initial_config>` file

The bot will run and print all logging information to stdout.
