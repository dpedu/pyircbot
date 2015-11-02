:mod:`DogeDice` --- A dogecoin game
===================================

Module to provide a game for gambling Dogecoin

.. code-block:: json

    {
        "minBet": 0.01,
        "lobbyIdleSeconds": 15,
        "channelWhitelistOn": true,
        "channelWhitelist": [
            "dogegamestest",
            "test"
        ]
    }

.. cmdoption:: lobbyIdleSeconds

    When more than 1 player has joined, the game will start after this many 
    seconds

Commands
--------

.. cmdoption:: .join <amount>

    Join the current round and bet <amount> dogecoins

.. cmdoption:: .leave

    Leave the current round. 

.. cmdoption:: .roll

    Once the game has started, roll the dice

Class Reference
---------------

.. automodule:: pyircbot.modules.DogeDice
    :members:
    :undoc-members:
    :show-inheritance:
