"""
.. module:: PyIRCBot
   :synopsis: Main IRC bot class

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import logging
import sys
from pyircbot.rpc import BotRPC
from pyircbot.irccore import IRCCore
from socket import AF_INET, AF_INET6
import os.path
import asyncio
import traceback


class ModuleLoader(object):
    def __init__(self):
        """storage of imported modules"""
        self.modules = {}

        """instances of modules"""
        self.moduleInstances = {}

        self.log = logging.getLogger('ModuleLoader')

    def importmodule(self, name):
        """Import a module

        :param moduleName: Name of the module to import
        :type moduleName: str"""
        " check if already exists "
        if name not in self.modules:
            self.log.info("Importing %s" % name)
            " attempt to load "
            try:
                moduleref = __import__(name)
                self.modules[name] = moduleref
                return (True, None)
            except Exception as e:
                " on failure (usually syntax error in Module code) print an error "
                self.log.error("Module %s failed to load: " % name)
                self.log.error("Module load failure reason: " + str(e))
                traceback.print_exc()
                return (False, str(e))
        else:
            self.log.warning("Module %s already imported" % name)
            return (False, "Module already imported")

    def deportmodule(self, name):
        """Remove a module's code from memory. If the module is loaded it will be unloaded silently.

        :param moduleName: Name of the module to import
        :type moduleName: str"""
        self.log.info("Deporting %s" % name)
        " unload if necessary "
        if name in self.moduleInstances:
            self.unloadmodule(name)
        " delete all references to the module"
        if name in self.modules:
            del self.modules[name]
            " delete copy that python stores in sys.modules "
            if name in sys.modules:
                del sys.modules[name]

    def loadmodule(self, name):
        """Activate a module.

        :param moduleName: Name of the module to activate
        :type moduleName: str"""
        " check if already loaded "
        if name in self.moduleInstances:
            self.log.warning("Module %s already loaded" % name)
            return False
        " check if needs to be imported, and verify it was "
        if name not in self.modules:
            importResult = self.importmodule(name)
            if not importResult[0]:
                return importResult
        " init the module "
        self.moduleInstances[name] = getattr(self.modules[name], name)(self, name)
        " load hooks "
        # self.loadModuleHooks(self.moduleInstances[name])
        self.moduleInstances[name].onenable()

    def unloadmodule(self, name):
        """Deactivate a module.

        :param moduleName: Name of the module to deactivate
        :type moduleName: str"""
        if name in self.moduleInstances:
            " notify the module of disabling "
            self.moduleInstances[name].ondisable()
            " unload all hooks "
            # self.unloadModuleHooks(self.moduleInstances[name])
            " remove & delete the instance "
            self.moduleInstances.pop(name)
            self.log.info("Module %s unloaded" % name)
            return (True, None)
        else:
            self.log.info("Module %s not loaded" % name)
            return (False, "Module not loaded")

    def reloadmodule(self, name):
        """Deactivate and activate a module.

        :param moduleName: Name of the target module
        :type moduleName: str"""
        " make sure it's imporeted"
        if name in self.modules:
            " remember if it was loaded before"
            loadedbefore = name in self.moduleInstances
            self.log.info("Reloading %s" % self.modules[name])
            " unload "
            self.unloadmodule(name)
            " load "
            if loadedbefore:
                self.loadmodule(name)
            return (True, None)
        return (False, "Module is not loaded")

    def redomodule(self, name):
        """Reload a running module from disk

        :param moduleName: Name of the target module
        :type moduleName: str"""
        " remember if it was loaded before "
        loadedbefore = name in self.moduleInstances
        " unload/deport "
        self.deportmodule(name)
        " import "
        importResult = self.importmodule(name)
        if not importResult[0]:
            return importResult
        " load "
        if loadedbefore:
            self.loadmodule(name)
        return (True, None)

    def getmodulebyname(self, name):
        """Get a module object by name

        :param name: name of the module to return
        :type name: str
        :returns: object -- the module object"""
        if name not in self.moduleInstances:
            return None
        return self.moduleInstances[name]

    def getmodulesbyservice(self, service):
        """Get a list of modules that provide the specified service

        :param service: name of the service searched for
        :type service: str
        :returns: list -- a list of module objects"""
        validModules = []
        for module in self.moduleInstances:
            if service in self.moduleInstances[module].services:
                validModules.append(self.moduleInstances[module])
        return validModules

    def getBestModuleForService(self, service):
        """Get the first module that provides the specified service

        :param service: name of the service searched for
        :type service: str
        :returns: object -- the module object, if found. None if not found."""
        m = self.getmodulesbyservice(service)
        if len(m) > 0:
            return m[0]
        return None


class PrimitiveBot(ModuleLoader):
    def __init__(self, botconfig):
        super().__init__()
        self.botconfig = botconfig

    def closeAllModules(self):
        """
        Deport all modules (for shutdown). Modules are unloaded in the opposite order listed in the config.
        """
        loaded = list(self.moduleInstances.keys())
        loadOrder = self.botconfig["modules"]
        loadOrder.reverse()
        for key in loadOrder:
            if key in loaded:
                loaded.remove(key)
                self.deportmodule(key)
        for key in loaded:
            self.deportmodule(key)

    " Filesystem Methods "
    def getConfigPath(self, moduleName):
        """Return the absolute path for a module's config file

        :param moduleName: the module who's config file we want
        :type moduleName: str"""

        basepath = "%s/config/%s" % (self.botconfig["bot"]["datadir"], moduleName)

        if os.path.exists("%s.json" % basepath):
            return "%s.json" % basepath
        return None

    def getDataPath(self, moduleName):
        """Return the absolute path for a module's data dir

        :param moduleName: the module who's data dir we want
        :type moduleName: str"""
        module_dir = os.path.join(self.botconfig["bot"]["datadir"], "data", moduleName)
        if not os.path.exists(module_dir):
            os.mkdir(module_dir)
        return module_dir


class PyIRCBot(PrimitiveBot):
    """:param botconfig: The configuration of this instance of the bot. Passed by main.py.
    :type botconfig: dict
    """
    version = "5.0.0"

    def __init__(self, botconfig):
        super().__init__(botconfig)

        self.log = logging.getLogger('PyIRCBot')
        """Reference to logger object"""

        self.loop = asyncio.get_event_loop()

        """Reference to BotRPC thread"""
        if self.botconfig["bot"]["rpcport"] >= 0:
            self.rpc = BotRPC(self)

        ratelimit = self.botconfig["connection"].get("rate_limit", None) or dict(rate_max=5.0, rate_int=1.1)

        """IRC protocol handler"""
        self.irc = IRCCore(servers=self.botconfig["connection"]["servers"],
                           loop=self.loop,
                           rate_limit=True if ratelimit else False,
                           rate_max=ratelimit["rate_max"],
                           rate_int=ratelimit["rate_int"])
        if self.botconfig.get("connection").get("force_ipv6", False):
            self.irc.connection_family = AF_INET6
        elif self.botconfig.get("connection").get("force_ipv4", False):
            self.irc.connection_family = AF_INET
        self.irc.bind_addr = self.botconfig.get("connection").get("bind", None)

        self.act_PONG = self.irc.act_PONG
        self.act_USER = self.irc.act_USER
        self.act_NICK = self.irc.act_NICK
        self.act_JOIN = self.irc.act_JOIN
        self.act_PRIVMSG = self.irc.act_PRIVMSG
        self.act_MODE = self.irc.act_MODE
        self.act_ACTION = self.irc.act_ACTION
        self.act_KICK = self.irc.act_KICK
        self.act_QUIT = self.irc.act_QUIT
        self.act_PASS = self.irc.act_PASS
        self.get_nick = self.irc.get_nick
        self.decodePrefix = IRCCore.decodePrefix

        # Load modules
        self.initModules()

        # Internal usage hook
        self.irc.addHook("_ALL", self._irchook_internal)

    def initModules(self):
        """load modules specified in instance config"""
        " append module location to path "
        sys.path.append(os.path.dirname(__file__) + "/modules/")

        " append usermodule dir to beginning of path"
        for path in self.botconfig["bot"]["usermodules"]:
            sys.path.insert(0, path + "/")

        for modulename in self.botconfig["modules"]:
            self.loadmodule(modulename)

    def run(self):
        self.client = asyncio.ensure_future(self.irc.loop(self.loop), loop=self.loop)
        try:
            self.loop.set_debug(True)
            self.loop.run_until_complete(self.client)
        finally:
            logging.debug("Escaped main loop")

    def disconnect(self, message):
        """Send quit message and disconnect from IRC.

        :param message: Quit message
        :type message: str
        :param reconnect: True causes a reconnection attempt to be made after the disconnect
        :type reconnect: bool
        """
        self.log.info("disconnect")
        self.kill(message=message)

    def kill(self, message="Help! Another thread is killing me :(", forever=True):
        """Close the connection violently

        :param sys_exit: True causes sys.exit(0) to be called
        :type sys_exit: bool
        :param message: Quit message
        :type message: str
        """
        if forever:
            self.closeAllModules()
        asyncio.run_coroutine_threadsafe(self.irc.kill(message=message, forever=forever), self.loop)

    def _irchook_internal(self, msg):
        """
        IRC hook handler. Calling point for IRCHook based module hooks. This method is called when any message is
        received. It tests all hooks in all modules against the message can calls the hooked function on hits.
        """
        for module_name, module in self.moduleInstances.items():
            for hook in module.irchooks:
                validation = hook.validator(msg, self)
                if validation:
                    hook.method(msg, validation)

    " Filesystem Methods "
    def getConfigPath(self, moduleName):
        """Return the absolute path for a module's config file

        :param moduleName: the module who's config file we want
        :type moduleName: str"""

        basepath = "%s/config/%s" % (self.botconfig["bot"]["datadir"], moduleName)

        if os.path.exists("%s.json" % basepath):
            return "%s.json" % basepath
        return None

    def getDataPath(self, moduleName):
        """Return the absolute path for a module's data dir

        :param moduleName: the module who's data dir we want
        :type moduleName: str"""
        module_dir = os.path.join(self.botconfig["bot"]["datadir"], "data", moduleName)
        if not os.path.exists(module_dir):
            os.mkdir(module_dir)
        return module_dir
