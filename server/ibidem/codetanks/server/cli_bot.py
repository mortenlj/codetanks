#!/usr/bin/env python
# -*- coding: utf-8

import argparse
from cmd import Cmd

import zmq

from ibidem.codetanks.domain.ttypes import Registration, ClientType, Id
from ibidem.codetanks.domain.util import serialize, deserialize


class CliBot(Cmd):
    prompt = "==> "
    intro = "Issue commands to your bot"

    def __init__(self, server_url):
        Cmd.__init__(self)
        zmq_context = zmq.Context.instance()
        registration_socket = zmq_context.socket(zmq.REQ)
        registration_socket.connect(server_url)
        registration_socket.send(serialize(Registration(ClientType.BOT, Id("clibot", 1))))
        reply = deserialize(registration_socket.recv())
        self._update_socket = zmq_context.socket(zmq.SUB)
        self._update_socket.set(zmq.SUBSCRIBE, "")
        update_url = reply.update_url
        print "Subscribing to %s" % update_url
        self._update_socket.connect(update_url)

    def do_EOF(self, line):
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("server_url")
    args = parser.parse_args()
    bot = CliBot(args.server_url)
    bot.cmdloop()

if __name__ == "__main__":
    main()
