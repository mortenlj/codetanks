#!/usr/bin/env python
# -*- coding: utf-8

import argparse

from gevent import sleep
import pinject
import goless
import zmq.green as zmq

from ibidem.codetanks.server.broker import Broker
from ibidem.codetanks.server.game_server import GameServer


class ObjectGraph(pinject.BindingSpec):
    def __init__(self, registration_port):
        self._registration_port = registration_port

    def configure(self, bind):
        bind("zmq_context", to_instance=zmq.Context.instance())
        bind("zmq_poller", to_class=zmq.Poller, in_scope=pinject.PROTOTYPE)
        bind("game_server_channel", to_instance=goless.chan())
        bind("update_channel", to_instance=goless.chan())
        bind("registration_port", to_instance=self._registration_port)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=13337)
    args = parser.parse_args()
    obj_graph = pinject.new_object_graph(binding_specs=[ObjectGraph(args.port)])
    for cls in [Broker, GameServer]:
        instance = obj_graph.provide(cls)
        goless.go(instance.run)
    sleep(60*2)

if __name__ == "__main__":
    main()
