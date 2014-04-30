#!/usr/bin/env python
# -*- coding: utf-8

from socket import gethostname

from pinject import copy_args_to_public_fields
import zmq


class Socket(object):
    @copy_args_to_public_fields
    def __init__(self, zmq_socket, port):
        pass

    @property
    def url(self):
        return "tcp://%s:%d" % (gethostname(), self.port)


def create_socket(zmq_context, socket_type, port):
    zmq_socket = zmq_context.socket(socket_type)
    if port:
        zmq_socket.bind("tcp://*:%d" % port)
    else:
        port = zmq_socket.bind_to_random_port("tcp://*")
    return Socket(zmq_socket, port)


class Broker(object):
    def __init__(self, zmq_context, zmq_poller, registration_port=None):
        self.registration_socket = create_socket(zmq_context, zmq.REP, registration_port)
        self.update_socket = create_socket(zmq_context, zmq.PUB, None)
        self.zmq_poller = zmq_poller
        self.zmq_poller.register(self.registration_socket)
        self.zmq_poller.register(self.update_socket)

if __name__ == "__main__":
    pass
