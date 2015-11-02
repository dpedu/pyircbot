:mod:`DogeScramble` --- A word scramble game with rewards
=========================================================

This module provides a word scrambling game that rewards winners with small
amounts of Dogecoin. Requires a ``dogerpc`` service provider such as 
:doc:`DogeRPC </api/modules/dogerpc>`.

Config
------

.. code-block:: json

    {
        "hintDelay": 15,
        "delayNext": 5,
        "maxHints": 5,
        "abortAfterNoGuesses": 2,
        "categoryduration": 10,
        "winAmount": 5,
        "decreaseFactor": 0.75
    }

In addition to the json config above, additional categories of words may be 
added by adding additional text files to the DogeScramble data dir.

.. cmdoption:: hintDelay

    Seconds between hints if the word is not guessed

.. cmdoption:: delayNext

    Delay in seconds between the end of one round and start of the next

.. cmdoption:: maxHints

    How many letters will be hinted before the word is thrown away

.. cmdoption:: abortAfterNoGuesses

    How many rounds may pass with no players guessing. Once this count is 
    passed, the game is automatically stopped.

.. cmdoption:: categoryduration

    Number of words used from a category before changing the category

.. cmdoption:: winAmount

    Amount of dogecoin to send the winner

.. cmdoption:: decreaseFactor

    For subsequent wins by the same player, the reward will be the previous
    reward multiplied times this number

Commands
--------

.. cmdoption:: .scramble

    Start the unscramble game

.. cmdoption:: .scrambleoff

    Stop the unscramble game

Class Reference
---------------

.. automodule:: pyircbot.modules.DogeScramble
    :members:
    :undoc-members:
    :show-inheritance:
