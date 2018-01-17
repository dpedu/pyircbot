#!/usr/bin/env python3

from contextlib import closing
from msgbus.client import MsgbusSubClient
import argparse
from time import sleep
from json import dumps


def main():
    parser = argparse.ArgumentParser(description="send irc art")
    parser.add_argument("-i", "--host", default="127.0.0.1", help="host to connect to")
    parser.add_argument("-p", "--port", default=7003, help="port to connect to")
    parser.add_argument("-c", "--channel", required=True, help="irc channel")
    parser.add_argument("-f", "--file", required=True, help="file containing irc lines to send")
    parser.add_argument("--delay", type=float, default=1.0, help="delay between lines (s)")
    parser.add_argument("--names", default=["default"], nargs="+", help="bot pubsub names to send via")
    parser.add_argument("--name-burst", default=1, type=int, help="num lines to send before choosing next name")
    parser.add_argument("--name-burst-delay", default=0.0, type=float, help="delay between single name bursts")
    parser.add_argument("--name-change-delay", type=float, default=0.0)
    args = parser.parse_args()

    with open(args.file) as f:
        with closing(MsgbusSubClient(args.host, args.port)) as client:
            name = 0
            per_name = 0
            for line in f:
                line = line.rstrip()
                print(line)
                client.pub("pyircbot_send", "{} privmsg {}".format(args.names[name], dumps([args.channel, line])))
                per_name += 1
                # if the current name has reached its quota
                if per_name >= args.name_burst:
                    # Do the main sleep
                    sleep(args.delay)
                    per_name = 0
                    # Advance to the next name
                    name += 1
                    if name >= len(args.names):
                        name = 0
                        if args.name_change_delay:
                            sleep(args.name_change_delay)
                else:
                    # Same name, do the burst delay
                    if args.name_burst_delay:
                        sleep(args.name_burst_delay)


if __name__ == '__main__':
    main()
