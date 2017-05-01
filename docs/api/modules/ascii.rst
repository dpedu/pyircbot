:mod:`ASCII` --- Ascii art database & spammer
=============================================

Prints ascii art to the channel

Setup
-----

Place .txt files in `datadir/ASCII/`. The file names must end in `.txt` and can contain alphanumerics, underscores,
and dashes. They must be UTF-8 decodable but will otherwise be transmitted verbatim.

Commands
--------

.. cmdoption:: .listascii

    List available ascii arts.

.. cmdoption:: .ascii <name>

    Begin printing the named ascii art

.. cmdoption:: .stopascii

    Stop the currently running ascii art

Class Reference
---------------

.. automodule:: pyircbot.modules.ASCII
    :members:
    :undoc-members:
    :show-inheritance:
