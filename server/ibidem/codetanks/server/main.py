#!/usr/bin/env python
# -*- coding: utf-8

import argparse

import zmq
from ibidem.codetanks.server import events

from ibidem.codetanks.server.game_server import GameServer


# Socket names
REGISTRATION = "registration"
UPDATE = "update"


class App(object):
    def __init__(self, registration_port):
        self._sockets = {}
        self._socket_urls = {}
        self._init_socket(zmq.REP, REGISTRATION, registration_port)
        self._init_socket(zmq.PUB, UPDATE)
        self.poller = zmq.Poller()
        self.poller.register(self._sockets[REGISTRATION])
        self.game_server = GameServer()

    def _init_socket(self, socket_type, name, port=None, zmq_context=None):
        if not zmq_context:
            zmq_context = zmq.Context.instance()
        self._sockets[name] = zmq_context.socket(socket_type)
        if port:
            self._sockets[name].bind("tcp://*:%d" % port)
        else:
            port = self._sockets[name].bind_to_random_port("tcp://*")
        url = "tcp://localhost:%d" % port
        self._socket_urls[name] = url
        print "Opened %s on %s" % (name, url)

    def run(self):
        while True:
            for event in events.get():
                if event == events.START_GAME:
                    self.game_server.start()

            socks = dict(self.poller.poll(1))
            reg_socket = self._sockets[REGISTRATION]
            if reg_socket in socks and socks[reg_socket] == zmq.POLLIN:
                registration = reg_socket.recv_json()
                print "Received registration: %r" % registration
                reg_socket.send_json({"update_url": self._socket_urls[UPDATE],
                                      "game_info": self.game_server.build_game_info()})

            if self.game_server.started():
                self.game_server.update()
                game_data = self.game_server.build_game_data()
                self._sockets[UPDATE].send_json(game_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int)
    args = parser.parse_args()
    app = App(args.port)
    app.run()

if __name__ == "__main__":
    main()
