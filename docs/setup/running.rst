*************
Running a bot
*************

The bot is invoked from the command line:

.. code-block:: sh

    ./pyircbot/main.py -c config.main.yml -b config.instance.yml

.. cmdoption:: -c --config

    Path to the "core" config file

.. cmdoption:: -b --bot

    Path to the "instance" config file

.. note:: A shell script, run-example.sh, is included in the source. This script
    should be renamed and can be used to run the bot.

The bot will run and print all logging information to stdout.
