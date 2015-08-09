from pyircbot.modulebase import ModuleBase,ModuleHook

class EchoExample(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.loadConfig()
        print(self.config)
        self.hooks=[ModuleHook("PRIVMSG", self.echo)]

    def echo(self, event):
        print(event)
        print(repr(event))
        print(dir(event))
        self.bot.act_PRIVMSG(event.args[0], event.trailing)

    def ondisable(self):
        print("I'm getting unloaded!")