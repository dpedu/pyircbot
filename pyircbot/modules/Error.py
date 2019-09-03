
"""
.. module:: Error
    :synopsis: Module to deliberately cause an error for testing handling.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, hook


class Error(ModuleBase):

    @hook("PRIVMSG")
    def error(self, message, command):
        """
        If the message recieved from IRC has the string "error" in it, cause a ZeroDivisionError
        """
        if "error" in message.trailing:
            print(10 / 0)

