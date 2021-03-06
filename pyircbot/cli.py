#!/usr/bin/env python3
import sys
import logging
import signal
from argparse import ArgumentParser
from pyircbot.common import load, sentry_sdk
from pyircbot import PyIRCBot
from json import loads


def main():
    " logging level and facility "
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)-15s %(levelname)-8s %(filename)s:%(lineno)d %(message)s")
    log = logging.getLogger('main')

    " parse command line args "
    parser = ArgumentParser(description="Run pyircbot")
    parser.add_argument("-c", "--config", help="Path to config file", required=True)
    parser.add_argument("--debug", action="store_true", help="Dump raw irc network")
    parser.add_argument("-q", "--quit-message", help="Quit message if killed by signal",
                        default="received signal {}")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    log.debug(args)

    if not args.config:
        log.critical("No bot config file specified (-c). Exiting.")
        sys.exit(1)

    botconfig = loads(sys.stdin.read()) if args.config == "-" else load(args.config)

    if sentry_sdk and "dsn" in botconfig["bot"]:
        sentry_sdk.init(botconfig["bot"]["dsn"])

    log.debug(botconfig)

    bot = PyIRCBot(botconfig)

    def signal_handler(signum, stack):
        print('Received:', signum)
        bot.kill(message=args.quit_message.format(signum))

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot.run()


if __name__ == "__main__":
    main()
