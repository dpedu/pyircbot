from pyircbot.modulebase import ModuleBase,ModuleHook

class EchoExample(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.loadConfig()
        print(self.config)
        self.hooks=[ModuleHook("PRIVMSG", self.echo)]

    def echo(self, args, prefix, trailing):
        self.bot.act_PRIVMSG(args[0], trailing)

    def ondisable(self):
        print("I'm getting unloaded!")