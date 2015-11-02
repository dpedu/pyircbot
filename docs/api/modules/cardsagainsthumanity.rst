:mod:`CardsAgainstHumanity` --- CaH in IRC
==========================================

IRC based Cards Against Humanity clone. Requires "black card" messages to be 
placed in file named ``questions.txt`` in the data dir, and "white card" messages
in a file named ``answers.txt``.

Commands
--------

.. cmdoption:: .joinGame

    If the game hasn't started yet, join the lobby

.. cmdoption:: .ready

    The game will start when all players are ready; this indicates a player is 
    ready

.. cmdoption:: .pick <card number> [<card number>] ...

    If the player is not the card czar, play one or more cards from their hand

.. cmdoption:: .choose <card number>

    If a player is the card czar, choose the winning card number

Class Reference
---------------

.. automodule:: pyircbot.modules.CardsAgainstHumanity
    :members:
    :undoc-members:
    :show-inheritance:
