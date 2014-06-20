#!/usr/bin/env python
# -*- coding: utf-8

from socket import gethostname

import zmq

from ibidem.codetanks.domain.util import deserialize, serialize


class ChannelType(object):
    REQUEST = zmq.REQ
    REPLY = zmq.REP
    PUBLISH = zmq.PUB
    SUBSCRIBE = zmq.SUB


class Channel(object):
    url_scheme = "tcp"
    url_wildcard = "*"

    def __init__(self, channel_type, port=None):
        ctx = zmq.Context.instance()
        self.zmq_socket = ctx.socket(channel_type)
        self.port = self._bind_socket(port)

    def _bind_socket(self, port):
        if port:
            self.zmq_socket.bind(self._create_url(self.url_wildcard, port))
        else:
            port = self.zmq_socket.bind_to_random_port(self._create_url(self.url_wildcard))
        return port

    def _create_url(self, host, port=None):
        url = "%s://%s" % (self.url_scheme, host)
        return "%s:%d" % (url, port) if port else url

    @property
    def url(self):
        return self._create_url(gethostname(), self.port)

    def ready(self):
        return self.zmq_socket.poll(1) == zmq.POLLIN

    def recv(self):
        data = self.zmq_socket.recv(copy=False)
        value = deserialize(data.buffer)
        return value

    def send(self, value):
        data = serialize(value)
        self.zmq_socket.send(data, copy=False)

if __name__ == "__main__":
    pass
