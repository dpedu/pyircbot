"""
.. module:: Error
    :synopsis: Module to deliberately cause an error for testing handling.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

#!/usr/bin/env python
from pyircbot.modulebase import ModuleBase,ModuleHook

class Error(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks=[ModuleHook("PRIVMSG", self.error)]
    
    def error(self, args, prefix, trailing):
        """If the message recieved from IRC has the string "error" in it, cause a ZeroDivisionError
        
        :param args: IRC args received
        :type args: list
        :param prefix: IRC prefix of sender
        :type prefix: str
        :param trailing: IRC message body
        :type trailing: str"""
        if "error" in trailing:
            print(10/0)

