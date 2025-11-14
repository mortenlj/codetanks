#!/usr/bin/env python
# -*- coding: utf-8
import sys
from collections import namedtuple
from typing import Optional

import zmq
from ibidem.codetanks.domain import messages_pb2
from ibidem.codetanks.domain.messages_pb2 import CommandReply, Command, Event, ClientType

from ibidem.codetanks.server import peer
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

    def wait(self):
        return self.zmq_socket.poll()

    def recv(self):
        data = self.zmq_socket.recv(copy=False)
        value = deserialize(self._clz(), data.buffer)
        return value

    def send(self, value):
        data = serialize(value)
        self.zmq_socket.send(data, copy=False)


class ZeroMQPeer(peer.Peer):
    id: messages_pb2.Id
    client_type: messages_pb2.ClientType

    def __init__(self, registration: messages_pb2.Registration, event_channel: Channel, cmd_channel: Channel):
        self.id = registration.id
        self.client_type = registration.client_type
        self._event_channel = event_channel
        self._cmd_channel = cmd_channel

    def handle_event(self, event: messages_pb2.Event) -> None:
        self._event_channel.send(event)

    def next_command(self) -> Optional[messages_pb2.Command]:
        if self._cmd_channel.ready():
            return self._cmd_channel.recv()
        return None

    def command_reply(self, reply: messages_pb2.CommandReply):
        self._cmd_channel.send(reply)


class ZeroMQServer:
    def __init__(self, registration_handler, viewer_channel, registration_channel):
        self._registration_handler = registration_handler
        self._viewer_channel = viewer_channel
        self._registration_channel = registration_channel

        event_port_range = settings.event_port_range
        cmd_port_range = settings.cmd_port_range
        self._publish_ports = iter(range(event_port_range[0], event_port_range[1] + 1))
        self._reply_ports = iter(range(cmd_port_range[0], cmd_port_range[1] + 1))
        self._peer_ids = iter(range(sys.maxsize))
        self._peers = {}
        self._game_info = None

    def _channel_factory(self, channel_type):
        if channel_type == ChannelType.PUBLISH:
            port = next(self._publish_ports)
        elif channel_type == ChannelType.REPLY:
            port = next(self._reply_ports)
        else:
            raise ValueError("Invalid channel type")
        return Channel(channel_type, port)

    def start(self):
        """TODO: Figure out how this should be started/run"""
        while True:
            if self._registration_channel.wait() == zmq.POLLIN:
                registration = self._registration_channel.recv()
                if registration.client_type == ClientType.VIEWER:
                    self._register_viewer(registration)
                else:
                    self._register_bot(registration)

    def _register_viewer(self, registration: messages_pb2.Registration):
        if self._game_info:
            registration_reply = messages_pb2.RegistrationReply(result=messages_pb2.RegistrationResult.SUCCESS,
                                                                game_info=self._game_info,
                                                                event_url=self._viewer_channel.url)
        else:
            peer = ZeroMQPeer(registration, self._viewer_channel, None)
            registration_reply: messages_pb2.RegistrationReply = self._registration_handler(peer)
            if registration_reply.result == messages_pb2.RegistrationResult.SUCCESS:
                self._game_info = registration_reply.game_info
        self._registration_channel.send(registration_reply)

    def _register_bot(self, registration: messages_pb2.Registration):
        event_channel = self._channel_factory(ChannelType.PUBLISH)
        cmd_channel = self._channel_factory(ChannelType.REPLY)
        peer = ZeroMQPeer(registration, event_channel, cmd_channel)
        peer_id = next(self._peer_ids)
        registration_reply: messages_pb2.RegistrationReply = self._registration_handler(peer)
        if registration_reply.result == messages_pb2.RegistrationResult.SUCCESS:
            self._peers[peer_id] = peer
            registration_reply.event_url = event_channel.url
            registration_reply.cmd_url = cmd_channel.url
        self._registration_channel.send(registration_reply)


def serialize(value):
    return value.SerializeToString()


def deserialize(cls, buffer):
    return cls.FromString(buffer)


if __name__ == "__main__":
    pass
