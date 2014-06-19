#!/usr/bin/env python
# -*- coding: utf-8

import argparse

import pinject

from ibidem.codetanks.server.com import Channel, SocketType
from ibidem.codetanks.server.game_server import GameServer


class ObjectGraph(pinject.BindingSpec):
    def __init__(self, registration_port):
        self._registration_port = registration_port

    def configure(self, bind):
        bind("registration_port", to_instance=self._registration_port)

    def provide_viewer_channel(self):
        return Channel(SocketType.PUBLISH)

    def provide_registration_channel(self, registration_port):
        return Channel(SocketType.REPLY, registration_port)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=13337)
    args = parser.parse_args()
    obj_graph = pinject.new_object_graph(binding_specs=[ObjectGraph(args.port)])
    game_server = obj_graph.provide(GameServer)
    game_server.run()

if __name__ == "__main__":
    main()
