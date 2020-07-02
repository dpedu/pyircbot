:mod:`StockIndex` --- DJIA and NASDAQ Quotes
============================================

This module provides quotes for the DJIA and NASDAQ indexes. It requires a free API key from
https://financialmodelingprep.com/


Commands
--------

.. cmdoption:: .djia

    Display the DJIA index

.. cmdoption:: .nasdaq

    Display the NASDAQ index


Config
------

.. code-block:: json

    {
        "apikey": "xxxxxxxxxxxxx",
        "cache_update_interval": 600,
        "cache_update_timeout": 10,
        "warning_thresh": 1800
    }

.. cmdoption:: apikey

    API ley obtained from https://financialmodelingprep.com/

.. cmdoption:: cache_update_interval

    How many seconds between fetching new index quotes from the API.

.. cmdoption:: cache_update_timeout

    Maximum seconds to wait on the HTTP request sent to the API

.. cmdoption:: warning_thresh

    A warning will be shown that the quote is out-of-date if the last successful fetch was longer ago than this
    setting's number of seconds.


Class Reference
---------------

.. automodule:: pyircbot.modules.StockIndex
    :members:
    :undoc-members:
    :show-inheritance:
