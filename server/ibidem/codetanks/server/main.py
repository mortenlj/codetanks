#!/usr/bin/env python
# -*- coding: utf-8

import logging
from datetime import timedelta

import pinject
from ibidem.codetanks.domain.messages_pb2 import Registration

from ibidem.codetanks.server import grpc_service
from ibidem.codetanks.server.config import settings
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.world import World
from ibidem.codetanks.server.zeromq import Channel, ChannelType, ZeroMQServer


class ObjectGraph(pinject.BindingSpec):
    def configure(self, bind):
        bind("world_width", to_instance=500)
        bind("world_height", to_instance=500)
        bind("registration_port", to_instance=settings.registration_port)
        bind("viewer_port", to_instance=settings.viewer_port)
        bind("event_port_range", to_instance=settings.event_port_range)
        bind("cmd_port_range", to_instance=settings.cmd_port_range)
        bind("debug", to_instance=settings.debug)
        bind("world", to_class=World)
        bind("zeromq_server", to_class=ZeroMQServer)
        bind("victory_delay", to_instance=timedelta(seconds=30))

    def provide_viewer_channel(self, viewer_port):
        return Channel(ChannelType.PUBLISH, viewer_port)

    def provide_registration_channel(self, registration_port):
        return Channel(ChannelType.REPLY, registration_port, Registration)

    def provide_channel_factory(self, event_port_range, cmd_port_range):
        publish_ports = [i for i in range(event_port_range[0], event_port_range[1] + 1)]
        reply_ports = [i for i in range(cmd_port_range[0], cmd_port_range[1] + 1)]

        def factory(channel_type):
            if channel_type == ChannelType.PUBLISH:
                port = publish_ports.pop(0)
            elif channel_type == ChannelType.REPLY:
                port = reply_ports.pop(0)
            else:
                raise ValueError("Invalid channel type")
            return Channel(channel_type, port)

        return factory


def main():
    loglevel = getattr(logging, settings.log_level.upper(), logging.INFO)
    if settings.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel)
    obj_graph = pinject.new_object_graph(modules=None, binding_specs=[ObjectGraph()])
    game_server = obj_graph.provide(GameServer)
    grpc_service.serve(game_server)
    game_server.run()


if __name__ == "__main__":
    main()
