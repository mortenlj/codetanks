#!/usr/bin/env python
# -*- coding: utf-8

import pytest
from mock import patch

from ibidem.codetanks.domain.messages_pb2 import Command, CommandType, Registration, ClientType, Id
from ibidem.codetanks.server.zeromq import Channel, ChannelType
from ibidem.codetanks.server.config import Settings


def _test_bind(self, port):
    """Hack to work around needing to use connect when testing"""
    if port:
        self.zmq_socket.bind(self._create_url(self.url_wildcard))
    else:
        self.zmq_socket.connect(self._create_url(self.url_wildcard))


class TestChannel(object):
    hostname = "test.example.com"
    port = 1234
    test_url_scheme = "inproc"

    @pytest.fixture
    def settings(self):
        return Settings(advertise_address=self.hostname)

    def test_has_valid_urls(self, settings):
        with patch("ibidem.codetanks.server.zeromq.settings", settings):
            socket = Channel(ChannelType.PUBLISH, self.port)
            assert socket.url == "tcp://%s:%d" % (self.hostname, self.port)

    def test_socket(self):
        with patch.object(Channel, "url_scheme", self.test_url_scheme), \
                patch.object(Channel, "url_wildcard", "test_socket"), \
                patch.object(Channel, "_bind_socket", _test_bind):
            req_socket = Channel(ChannelType.REQUEST, 1)
            rep_socket = Channel(ChannelType.REPLY, 0)
            value = Command(type=CommandType.FIRE)
            req_socket.send(value)
            assert rep_socket.recv() == value

    def test_socket_with_special_class(self):
        with patch.object(Channel, "url_scheme", self.test_url_scheme), \
                patch.object(Channel, "url_wildcard", "test_socket_with_special_class"), \
                patch.object(Channel, "_bind_socket", _test_bind):
            req_socket = Channel(ChannelType.REQUEST, 1)
            rep_socket = Channel(ChannelType.REPLY, 0, Registration)
            value = Registration(client_type=ClientType.VIEWER, id=Id(name="test", version=1))
            req_socket.send(value)
            assert rep_socket.recv() == value
