:mod:`SMS` --- A simple SMS client
==================================

This module provides ".text-<name> <message>" commands that send SMS messages
via the Twilio api.


Config
------

.. code-block:: json

    {
        "account_sid": "xxxx",
        "auth_token": "xxxx",
        "number": "+10000000000",
        "api_port": 3000,
        "channel": "#foo",
        "contacts": {
            "guy1": "+11111111111",
            "guy2": "+12222222222"
        },
        "limit": {
            "enable": true,
            "period": 900,
            "max": 5
        }
    }

.. cmdoption:: account_sid

    Twilio account ID

.. cmdoption:: auth_token

    Twilio auth token

.. cmdoption:: number

    Twilio phone number. Must match the format shown above.

.. cmdoption:: api_port

    HTTP port to listen for Twilio webhook requests on. Using `-1` disables webhook listening.

.. cmdoption:: channel

    Channel the module is enabled on

.. cmdoption:: contacts

    Dict of names to phone numbers. Names must be a-zA-Z0-9 and numbers match the format shown above.

.. cmdoption:: limit.enable

    Enable or disable rate limiting. Rate limiting is controlled as a "burst bucket." If enabled, sending an SMS
    requires 1 and removes one point from the bucket.

.. cmdoption:: limit.period

    Every `limit.period`, a virtual point is added to the bucket.

.. cmdoption:: limit.max

    When adding a point the bucket, the point will be discarded if the bucket already has `limit.max` points.


Twilio Setup
------------

In Twilio's UI, create a "Messaging Service" of the "Notifications, 2-Way"
type. Check "Process inbound messages" if desired and enter the bot's webhook
URL.

The webhook listener listens on `/app/gotsms`, so an example webhook URL would
be `http://1.2.3.4:3000/app/gotsms`.


Class Reference
---------------

.. automodule:: pyircbot.modules.SMS
    :members:
    :undoc-members:
    :show-inheritance:
