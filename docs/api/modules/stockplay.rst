:mod:`StockPlay` --- Simulated stock trading game
=================================================

This module provides a simulated stock trading game. Requires and api key from
https://www.alphavantage.co/ to fetch stock quotes.

Most commands require that the player login as described in the NickUser module.

Note that it is important to configure api limitations when configuring this module. The alphavantage.co api allows a
maximum of 5 requests per minute and 500 requests per day. For reporting reasons we need to keep the prices of all
traded symbols reasonably up-to-date (see *bginterval*). This happens at some interval.

Considering the daily limit means, when evenly spread, we can sent a request *no more often* than 173 seconds:
(24 * 60 * 60 / 500) - and therefore, the value of *bginterval* must be some value larger than 173, as this value will
completely consume the daily limit leaving no room for normal trades.


Commands
--------

.. cmdoption:: .buy <amount> <symbol>

    Buy some number of the specified stock symbol such as ".buy 10 amd"

.. cmdoption:: .sell <amount> <symbol>

    Sell similar to .buy

.. cmdoption:: .bal

    Show a summary report on the value of the player's cash + stock holdings

.. cmdoption:: .cash

    Show the player's cash balance

.. cmdoption:: .port

    Get a report on the player's portfolio. Value based on stocks may be delayed based on the *rcachesecs*
    config setting.


Config
------

.. code-block:: json

    {
        "startbalance": 10000,
        "tradedelay": 0,
        "apikey": "xxxxxxxxxxxxxx",
        "tcachesecs": 300,
        "rcachesecs": 14400,
        "bginterval": 300
    }

.. cmdoption:: startbalance

    Number of dollars that players start with

.. cmdoption:: tradedelay

    Delay in seconds between differing trades of the same symbol. Multiple buys OR multiple sells are allowed, but
    not a mix.

    NOT IMPLEMENTED

.. cmdoption:: apikey

    API key from https://www.alphavantage.co/support/#api-key

.. cmdoption:: tcachesecs

    When performing a trade, how old of a cached stock value is permitted before fetching from API.

    Recommended ~30 minutes (1800)

.. cmdoption:: rcachesecs

    When calculating a portfolio report, how old of a cached stock value is permitted before fetching from API.

    Recommended ~4 hours (14400)

.. cmdoption:: bginterval

    Symbol prices are updated in the background. This is necessary because fetching a portfolio report may require
    fetching many symbol prices. The alphavantage.co api allows only 5 calls per minute. Because of this limitation,
    fetching a report would take multiple minutes with more than 5 symbols, which would not work.

    For this reason, we update symbols at a low interval in the background. Every *bginterval* seconds, a task will be
    started that updates the price of symbols older than *rcachesecs*.

    Estimated 5 minute (300), but likely will need tuning depending on playerbase


Class Reference
---------------

.. automodule:: pyircbot.modules.StockPlay
    :members:
    :undoc-members:
    :show-inheritance:
