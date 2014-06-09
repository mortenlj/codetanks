#!/usr/bin/env python
# -*- coding: utf-8
from gevent import sleep
from goless import dcase, rcase, select
import zmq.green as zmq

from ibidem.codetanks.server.com import create
from ibidem.codetanks.domain import ttypes


class Broker(object):
    def __init__(self, zmq_context, zmq_poller, game_server_channel, viewer_channel, registration_port):
        self.registration_socket = create(zmq_context, zmq.REP, registration_port)
        self.viewer_socket = create(zmq_context, zmq.PUB, None)
        self.zmq_poller = zmq_poller
        self.zmq_poller.register(self.registration_socket.zmq_socket)
        self.zmq_poller.register(self.viewer_socket.zmq_socket)
        self.game_server_channel = game_server_channel
        self.viewer_channel = viewer_channel
        self.dcase = dcase()
        self.cases = {
            self.dcase: lambda x: x,
            rcase(self.viewer_channel): self.viewer_socket.send
        }

    def run(self):
        print "Broker starting, listening for registrations on %s" % self.registration_socket.url
        while True:
            self._run_once()

    def _check_sockets(self):
        socks = self.zmq_poller.poll(1)
        for pair in socks:
            if pair == (self.registration_socket.zmq_socket, zmq.POLLIN):
                event = self.registration_socket.recv()
                self.registration_socket.send(ttypes.RegistrationReply(self.viewer_socket.url))
                self.game_server_channel.send(event)

    def _check_channels(self):
        case, value = select(self.cases.keys())
        while case != self.dcase:
            func = self.cases[case]
            func(value)
            case, value = select(self.cases.keys())

    def _run_once(self):
        self._check_sockets()
        sleep(.01)
        self._check_channels()
        sleep(.01)

if __name__ == "__main__":
    pass
