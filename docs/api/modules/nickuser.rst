:mod:`NickUser` --- A simple authentication service
===================================================

A module providing a simple login/logout account service. "Trust" is based upon
hostname - logging in autorizes your current hostname for your account data, 
which is tied to your nick.

Commands
--------

.. cmdoption:: .setpass <oldpass> <newpass>

    Set or change your password. Users with a password already must provide the
    old password to set a new one.

.. cmdoption:: .login <password>

    Log into your account (authorize your current hostname)

.. cmdoption:: .logout

    Log out of account (deauthorize your current hostname)

Class Reference
---------------

.. automodule:: pyircbot.modules.NickUser
    :members:
    :undoc-members:
    :show-inheritance:
