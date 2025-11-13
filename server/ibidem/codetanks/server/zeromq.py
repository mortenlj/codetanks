#!/usr/bin/env python
# -*- coding: utf-8

from collections import namedtuple

import zmq

from ibidem.codetanks.domain.messages_pb2 import CommandReply, Command, Event
from ibidem.codetanks.server.config import settings


class ChannelType(object):
    _Type = namedtuple("_Type", ["socket", "clz"])
    REQUEST = _Type(zmq.REQ, CommandReply)
    REPLY = _Type(zmq.REP, Command)
    PUBLISH = _Type(zmq.PUB, None)
    SUBSCRIBE = _Type(zmq.SUB, Event)


class Channel(object):
    url_scheme = "tcp"
    url_wildcard = "*"

    def __init__(self, channel_type, port=None, override_clz=None):
        ctx = zmq.Context.instance()
        self._clz = override_clz or channel_type.clz
        self.zmq_socket = ctx.socket(channel_type.socket)
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
        return self._create_url(settings.advertise_address, self.port)

    def ready(self):
        return self.zmq_socket.poll(1) == zmq.POLLIN

    def recv(self):
        data = self.zmq_socket.recv(copy=False)
        value = deserialize(self._clz(), data.buffer)
        return value

    def send(self, value):
        data = serialize(value)
        self.zmq_socket.send(data, copy=False)


def serialize(value):
    return value.SerializeToString()


def deserialize(cls, buffer):
    return cls.FromString(buffer)


if __name__ == "__main__":
    pass
