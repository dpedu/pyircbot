:mod:`BotRPC` --- JSON RPC Controller
=====================================

PyIRCBot has a json rpc interface for controlling some aspects of the bot
remotely via JSON-RPC.

It's important to know the different states a module can be in.

- **Deported** - Module's code exists on disk but has not been read
- **Imported** - Module's code exists in memory but has not been instantiated
- **Loaded** - Module's code exists in memory and has been instantiated. "Running" modules are of this state.

.. automodule:: core.rpc
    :members:
    :undoc-members:
    :show-inheritance:
