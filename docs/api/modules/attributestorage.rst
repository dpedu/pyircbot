:mod:`AttributeStorage` --- Item key/value storage
==================================================

Item key->value storage engine based on mysql. Provides a service called
`attributes` that stores items.

Items are dicts. An item can have many keys. Each key points to one value.

.. code-block:: text

    [ item ] --+--> [ key ] --> [ value ]
               |
               +--> [ key ] --> [ value ]
               |
               +--> [ key ] --> [ value ]
    

.. automodule:: pyircbot.modules.AttributeStorage
    :members:
    :undoc-members:
    :show-inheritance:
