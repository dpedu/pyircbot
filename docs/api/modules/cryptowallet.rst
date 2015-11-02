:mod:`CryptoWallet` --- BitcoinD RPC Service
============================================

Module to provide a multi-type cryptocurrency wallet

Config
------

.. code-block:: json

    {
        "types": {
            "BTC": {
                "name": "Bitcoin",
                "abbr": "BTC",
                "host": "192.168.1.210",
                "username": "bobby",
                "password": "propane",
                "port": 8332,
                "precision": 8,
                "reserve": 0.0005,
                "link": "https://bitcoin.org/"
            }
        }
    }

.. cmdoption:: types

    Dictionary of supported crypto currencies, keyed abbreviation => detail. All fields required.

.. cmdoption:: types.TYPE.precision

    Number of decimal places the currency supports

.. cmdoption:: types.TYPE.reserve:

    Minimum balance; this is to cover tx fees

Commands
--------

.. cmdoption:: .curinfo [<currency>]

    See list of supported currencies, or info about a specific one.

.. cmdoption:: .getbal <currency>

    Get current user's balance of a specific currency

.. cmdoption:: .setaddr <currency> <address>

    Set current user's withdrawal address for <currency> to <address>

.. cmdoption:: .withdraw <currency> <amount>

    Request a withdrawal of <amount> to current user's withdraw address of <currency>

.. cmdoption:: .getaddr <currency>

    Get deposit address for <currency>

Class Reference
---------------

.. automodule:: pyircbot.modules.CryptoWallet
    :members:
    :undoc-members:
    :show-inheritance:
