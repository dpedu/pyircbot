:mod:`Services` --- Module to provide nick and channel services
===============================================================

Services enables the bot to:

 - Set it's nick on startup, and fall back to other names if one nick is taken
 - Identify with nickserv or similar
 - Ghost users using it's nick
 - Request invites & join private channels


Config
------

.. code-block:: json

    {
        "user":{
            "nick":[
                "pyircbot3",
                "pyircbot3_",
                "pyircbot3__"
            ],
            "password":"nickservpassword",
            "username":"pyircbot3",
            "hostname":"pyircbot3.domain.com",
            "realname":"pyircbot3"
        },
        "ident":{
            "enable":"no",
            "to":"nickserv",
            "command":"identify %(password)s",
            "ghost":"no",
            "ghost_to":"nickserv",
            "ghost_cmd":"ghost %(nick)s %(password)s"
        },
        "channels":[
            "#xmopx"
        ],
        "privatechannels":{
            "to":"chanserv",
            "command":"invite %(channel)s",
            "list":[
                "#aprivatechannel"
            ]
        }
    }

.. cmdoption:: user.nick

    A list of nicks, the first being the preferred nick and the others being
    fallbacks if the primary nick is taken.

.. cmdoption:: user.password

    Nickserv password

.. cmdoption:: user.username

    IRC username

.. cmdoption:: user.hostname

    Host name for the USER command

.. cmdoption:: user.realname

    IRC real name

.. cmdoption:: ident.enable

    Yes/no if you want to identify with Nickserv or another nick-protection
    entity

.. cmdoption:: ident.to

    Nick the identify command will be sent to

.. cmdoption:: ident.command

    String formatted command to be sent for identification. Available tokens:
     - password

.. cmdoption:: ident.ghost

    Yes/no if the bot should attempt to ghost anyone using it's nickname

.. cmdoption:: ident.ghost_to

    Nick the ghost command will be sent to

.. cmdoption:: ident.ghostcmd

    String formatted command to be sent for ghosting. Available tokens:
     - nick
     - password

.. cmdoption:: channels

    List of channels to join on startup

.. cmdoption:: privatechannels.to

    Nick to send the invite command to

.. cmdoption:: privatechannels.command

    String formatted command to be sent for invitations. Available tokens:
     - channel

.. cmdoption:: privatechannels.list

    List of channels to request an invite to join on startup


Service
-------

The ``service`` service provides information about the state of IRC. Available service methods:

.. cmdoption:: nick()

    Returns the current nick of the bot


Class Reference
---------------

.. automodule:: pyircbot.modules.Services
    :members:
    :undoc-members:
    :show-inheritance:
