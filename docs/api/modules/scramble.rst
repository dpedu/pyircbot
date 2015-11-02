:mod:`Scramble` --- Word scramble game module
=============================================

Example usage:

.. code-block:: none

    3:04:00 PM <@dave-irccloud> .scrambleon
    3:04:00 PM <pyircbot3> New word - leppa 
    3:04:15 PM <pyircbot3> Hint: - a____
    3:04:30 PM <pyircbot3> Hint: - ap___
    3:04:32 PM <@dave-irccloud> apple
    3:04:32 PM <pyircbot3> dave-irccloud guessed the word - apple! dave-irccloud now has 3 points. Next word in 5 seconds.
    3:04:35 PM <@dave-irccloud> .scrambleoff
    3:04:39 PM <@dave-irccloud> .scramble top
    3:04:39 PM <pyircbot3> Top 1: dave-irccloud: 3

Requires a dictionary to pull words from, ``words.txt`` should be placed in: ``./datadir/data/Scramble/``

Class Reference
---------------

.. automodule:: pyircbot.modules.Scramble
    :members:
    :undoc-members:
    :show-inheritance:
