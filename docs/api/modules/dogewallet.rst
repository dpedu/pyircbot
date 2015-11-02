:mod:`DogeWallet` --- A Dogecoin wallet
=======================================

This module provides a dogecoin wallet hosted on the IRC bot's server. Using 
:doc:`CryptoWallet </api/modules/cryptowallet>` instead is reccommended, this
has many command conflicts with newer modules.

Commands
--------

.. cmdoption:: .setpass (<newpass>|<oldpass> <newpass>)

    Create account or change password if account already exists. "Trust" is 
    based on user's hostname.

.. cmdoption:: .login <password>

    Log into the bot (just this module)

.. cmdoption:: .logout

    Log out

.. cmdoption:: .setdogeaddr <address>

    Set withdrawal address for current user

.. cmdoption:: .getdogebal

    Get current user's balance

.. cmdoption:: .withdrawdoge <password> <amount>

    With the right <password>, withdraw <amount> to current user's withdrawal 
    address

.. cmdoption:: .getdepositaddr

    Get current user's withdrawal address

Class Reference
---------------

.. automodule:: pyircbot.modules.DogeWallet
    :members:
    :undoc-members:
    :show-inheritance:
