#!/usr/bin/env python
# -*- coding: utf-8

from socket import gethostname

from gevent import sleep
from goless import dcase, rcase, select
import zmq.green as zmq

from ibidem.codetanks.domain import ttypes
from ibidem.codetanks.domain.util import serialize, deserialize


class Socket(object):
    def __init__(self, zmq_socket, port):
        self.zmq_socket = zmq_socket
        self.port = port

    @property
    def url(self):
        return "tcp://%s:%d" % (gethostname(), self.port)

    def recv(self):
        data = self.zmq_socket.recv()
        value = deserialize(data)
        return value

    def send(self, value):
        data = serialize(value)
        self.zmq_socket.send(data)


def create_socket(zmq_context, socket_type, port):
    zmq_socket = zmq_context.socket(socket_type)
    if port:
        zmq_socket.bind("tcp://*:%d" % port)
    else:
        port = zmq_socket.bind_to_random_port("tcp://*")
    return Socket(zmq_socket, port)


class Broker(object):
    def __init__(self, zmq_context, zmq_poller, game_server_channel, update_channel, registration_port):
        self.registration_socket = create_socket(zmq_context, zmq.REP, registration_port)
        self.update_socket = create_socket(zmq_context, zmq.PUB, None)
        self.zmq_poller = zmq_poller
        self.zmq_poller.register(self.registration_socket.zmq_socket)
        self.zmq_poller.register(self.update_socket.zmq_socket)
        self.game_server_channel = game_server_channel
        self.update_channel = update_channel
        self.dcase = dcase()
        self.cases = {
            self.dcase: lambda x: x,
            rcase(self.update_channel): self.update_socket.send
        }

    def run(self):
        print "Broker starting"
        while True:
            self._run_once()

    def _check_sockets(self):
        socks = self.zmq_poller.poll(1)
        for pair in socks:
            if pair == (self.registration_socket.zmq_socket, zmq.POLLIN):
                event = self.registration_socket.recv()
                self.registration_socket.send(ttypes.RegistrationReply(self.update_socket.url))
                self.game_server_channel.send(event)

    def _check_channels(self):
        case = None
        while case != self.dcase:
            case, value = select(self.cases.keys())
            func = self.cases[case]
            func(value)

    def _run_once(self):
        self._check_sockets()
        sleep(.01)
        self._check_channels()
        sleep(.01)

if __name__ == "__main__":
    pass
