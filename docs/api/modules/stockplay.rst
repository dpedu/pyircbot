:mod:`StockPlay` --- Stock-like trading game
============================================

This module provides a simulated stock trading game. Requires and api key from
https://www.alphavantage.co/ to fetch stock quotes.

Most commands require that the player login as described in the NickUser module.

Note that it is important to configure api limitations when configuring this module. The alphavantage.co api allows a
maximum of 5 requests per minute and 500 requests per day. For reasonable trading - that is, executing trades at the
current market price - we need to be able to lookup the price of any symbol at any time. Likewise, to generate reports
we need to keep the prices of all symbols somewhat up to date. This happens at some interval - see *bginterval*.

Considering the daily limit means, when evenly spread, we can sent a request *no more often* than 173 seconds:
`(24 * 60 * 60 / 500)` - and therefore, the value of *bginterval* must be some value larger than 173, as this value will
completely consume the daily limit.

When trading, the price of the traded symbol is allowed to be *trade_cache_seconds* seconds old before the API will be
used to fetch a more recent price. This value must be balanced against *bginterval* depending on your trade frequency
and variety.

Background or batch-style tasks that rely on symbol prices run afoul with the above constraints - but in a
magnified way as they rely on api-provided data to calculate player stats across many players at a time.


Commands
--------

.. cmdoption:: .buy <amount> <symbol>

    Buy some number of the specified symbol such as ".buy 10 amd"

.. cmdoption:: .sell <amount> <symbol>

    Sell similar to .buy

.. cmdoption:: .port [<player>] [<full>]

    Get a report on the calling player's portfolio. Another player's name can be passed as an argument to retrieve
    information about a player other than the calling player. Finally, the 'full' argument can be added to retrieve a
    full listing of the player's holdings.


Config
------

.. code-block:: json

    {
        "startbalance": 10000,
        "tradedelay": 0,
        "trade_cache_seconds": 300,
        "bginterval": 300,
        "announce_trades": false,
        "announce_channel": "#trades",
        "providers": [
            {
                "provider": "iexcloud",
                "apikey": "xxxxxxxxxxxxxxx"
            },
            {
                "provider": "alphavantage",
                "apikey": "xxxxxxxxxxxxxxx"
            }
        ]
    }

.. cmdoption:: startbalance

    Number of dollars that players start with

.. cmdoption:: tradedelay

    Delay in seconds between differing trades of the same symbol. Multiple buys OR multiple sells are allowed, but
    not a mix.

    NOT IMPLEMENTED

.. cmdoption:: providers

    A list of providers to fetch stock data from

    Supported providers:

        * https://www.alphavantage.co/
        * https://iexcloud.io/

.. cmdoption:: trade_cache_seconds

    When performing a trade, how old of a cached symbol price is permitted before fetching from API.

    Recommended ~30 minutes (1800)

.. cmdoption:: bginterval

    Symbol prices are updated in the background. This is necessary because fetching a portfolio report may require
    fetching many symbol prices. The alphavantage.co api allows only 5 calls per minute. Because of this limitation,
    fetching a report would take multiple minutes with more than 5 symbols, which would not work.

    For this reason, we update symbols at a low interval in the background. Every *bginterval* seconds, a task will be
    started that updates the price of the oldest symbol.

    Estimated 5 minute (300), but likely will need tuning depending on playerbase

.. cmdoption:: midnight_offset

    Number of seconds **added** to the clock when calculating midnight.

    At midnight, the bot logs all player balances for use in gain/loss over time calculations later on. If you want this
    to happen at midnight system time, leave this at 0. Otherwise, it can be set to some number of seconds to e.g. to
    compensate for time zones.

    Default: 0

.. cmdoption:: announce_trades

    Boolean option to announce all trades in a specific channel.

    Default: false

.. cmdoption:: announce_channel

    Channel name to announce all trades in.

    Default: not set


Class Reference
---------------

.. automodule:: pyircbot.modules.StockPlay
    :members:
    :undoc-members:
    :show-inheritance:
