#!/usr/bin/env python
# -*- coding: utf-8
from functools import wraps
import shlex
import argparse
import inspect
from cmd import Cmd

import zmq

from ibidem.codetanks.domain.ttypes import Registration, ClientType, Id, Move, Rotate, CommandResult, Aim
from ibidem.codetanks.domain.util import serialize, deserialize


class NoExitArgumentParser(argparse.ArgumentParser):
    class InvalidArguments(Exception):
        pass

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message)
        raise NoExitArgumentParser.InvalidArguments(message)


def parse_args(func):
    name = func.__name__[3:]
    args, varargs, kwargs, defaults = inspect.getargspec(func)
    args.remove("self")
    assert len(args) == len(defaults), "You must supply example value for all args of %s" % name
    assert None not in defaults, "You can't use None as an example value in %s" % name
    parser = NoExitArgumentParser(prog=name, add_help=False)
    for name, value in zip(args, defaults):
        parser.add_argument(name, type=type(value))
    @wraps(func)
    def wrapper(self, line):
        try:
            params = parser.parse_args(shlex.split(line))
            call_args = [getattr(params, name) for name in args]
            return func(self, *call_args)
        except NoExitArgumentParser.InvalidArguments:
            return False
    return wrapper


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
        event_url = reply.event_url
        print "Subscribing to %s" % event_url
        self._update_socket.connect(event_url)
        self._cmd_socket = zmq_context.socket(zmq.REQ)
        self._cmd_socket.connect(reply.cmd_url)
        print "Connecting to %s" % reply.cmd_url

    def _print_result(self):
        reply = deserialize(self._cmd_socket.recv())
        print "OK" if reply.result == CommandResult.OK else "BUSY"

    def do_exit(self, line):
        """Leave the bot-cli. Your bot will be left in whatever state it is in."""
        return True
    do_EOF = do_exit

    @parse_args
    def do_move(self, distance=10):
        self._cmd_socket.send(serialize(Move(distance)))
        self._print_result()

    @parse_args
    def do_rotate(self, angle=1.0):
        self._cmd_socket.send(serialize(Rotate(angle)))
        self._print_result()

    @parse_args
    def do_aim(self, angle=1.0):
        self._cmd_socket.send(serialize(Aim(angle)))
        self._print_result()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("server_url")
    args = parser.parse_args()
    bot = CliBot(args.server_url)
    bot.cmdloop()

if __name__ == "__main__":
    main()
