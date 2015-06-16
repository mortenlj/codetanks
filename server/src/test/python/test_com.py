#!/usr/bin/env python
# -*- coding: utf-8

from mock import patch
from hamcrest import assert_that, equal_to
from ibidem.codetanks.domain.ttypes import Command, CommandType, Registration, ClientType, Id

from ibidem.codetanks.server.com import Channel, ChannelType


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
    test_url_wildcard = "socket"

    def test_has_valid_urls(self):
        with patch("ibidem.codetanks.server.com.gethostname", return_value=self.hostname):
            socket = Channel(ChannelType.PUBLISH, self.port)
            assert_that(socket.url, equal_to("tcp://%s:%d" % (self.hostname, self.port)))

    def test_socket(self):
        with patch.object(Channel, "url_scheme", self.test_url_scheme), \
             patch.object(Channel, "url_wildcard", self.test_url_wildcard), \
             patch.object(Channel, "_bind_socket", _test_bind):
            req_socket = Channel(ChannelType.REQUEST, 1)
            rep_socket = Channel(ChannelType.REPLY, 0)
            value = Command(CommandType.FIRE)
            req_socket.send(value)
            assert_that(rep_socket.recv(), equal_to(value))

    def test_socket_with_special_class(self):
        with patch.object(Channel, "url_scheme", self.test_url_scheme), \
             patch.object(Channel, "url_wildcard", self.test_url_wildcard), \
             patch.object(Channel, "_bind_socket", _test_bind):
            req_socket = Channel(ChannelType.REQUEST, 1)
            rep_socket = Channel(ChannelType.REPLY, 0, Registration)
            value = Registration(ClientType.VIEWER, Id("test", 1))
            req_socket.send(value)
            assert_that(rep_socket.recv(), equal_to(value))

if __name__ == "__main__":
    import nose
    nose.main()
