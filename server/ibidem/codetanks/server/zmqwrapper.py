#!/usr/bin/env python
# -*- coding: utf-8

from socket import gethostname

from ibidem.codetanks.domain.util import deserialize, serialize


class Socket(object):
    def __init__(self, zmq_socket, port):
        self.zmq_socket = zmq_socket
        self.port = port

    @property
    def url(self):
        return "tcp://%s:%d" % (gethostname(), self.port)

    def recv(self):
        data = self.zmq_socket.recv(copy=False)
        value = deserialize(data.buffer)
        return value

    def send(self, value):
        data = serialize(value)
        self.zmq_socket.send(data, copy=False)


def create_socket(zmq_context, socket_type, port):
    zmq_socket = zmq_context.socket(socket_type)
    if port:
        zmq_socket.bind("tcp://*:%d" % port)
    else:
        port = zmq_socket.bind_to_random_port("tcp://*")
    return Socket(zmq_socket, port)

if __name__ == "__main__":
    pass
