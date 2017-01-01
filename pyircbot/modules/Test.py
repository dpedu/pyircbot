#!/usr/bin/env python
"""
.. module:: Test
    :synopsis: For testing code

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook


class Test(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks = [ModuleHook("PRIVMSG", self.dotest)]

    def dotest(self, args):
        print("DOTEST(%s)" % (args,))
