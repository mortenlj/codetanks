#!/usr/bin/env python
# -*- coding: utf-8

import argparse
from datetime import timedelta
import logging

from ibidem.codetanks.domain.messages_pb2 import Registration
import pinject
from ibidem.codetanks.server.com import Channel, ChannelType
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.world import World


class ObjectGraph(pinject.BindingSpec):
    @pinject.copy_args_to_internal_fields
    def __init__(self, registration_port, debug):
        pass

    def configure(self, bind):
        bind("world_width", to_instance=500)
        bind("world_height", to_instance=500)
        bind("registration_port", to_instance=self._registration_port)
        bind("debug", to_instance=self._debug)
        bind("world", to_class=World)
        bind("victory_delay", to_instance=timedelta(seconds=30))

    def provide_viewer_channel(self):
        return Channel(ChannelType.PUBLISH)

    def provide_registration_channel(self, registration_port):
        return Channel(ChannelType.REPLY, registration_port, Registration)

    def provide_channel_factory(self):
        def factory(channel_type):
            return Channel(channel_type)
        return factory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=13337)
    parser.add_argument("--debug", action="store_true", help="Enable debug features")
    parser.add_argument("--debuglogs", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    loglevel = logging.INFO
    if args.debug or args.debuglogs:
        loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel)
    obj_graph = pinject.new_object_graph(modules=None, binding_specs=[ObjectGraph(args.port, args.debug)])
    game_server = obj_graph.provide(GameServer)
    game_server.run()


if __name__ == "__main__":
    main()
