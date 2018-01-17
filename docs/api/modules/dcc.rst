:mod:`DCC` --- Interface to DCC file transfers
==============================================


A module providing a high-level interface for DCC file transfers.

DCC file transfers involve having the sender listen on some tcp port and the receiver connect to the port to initiate
the file transfer. The file name and length as well as the tcp port and address are shared via other means.


Config
------

.. code-block:: json

    {
        "port_range": [40690, 40990],
        "public_addr": "127.0.0.1",
        "bind_host": "127.0.0.1"
    }

.. cmdoption:: port_range

    The range of ports between which arbitrary ports will be used for file transfers

.. cmdoption:: public_addr

    When sending files, what address we will advertise as being connectable on

.. cmdoption:: bind_host

    What IP address to bind to when creating listener sockets for the file send role.


Class Reference
---------------

.. automodule:: pyircbot.modules.DCC
    :members:
    :undoc-members:
    :show-inheritance:
