#!/usr/bin/env python
# -*- coding: utf-8

from mock import patch
from nose.tools import eq_

from ibidem.codetanks.domain.ttypes import Id
from ibidem.codetanks.server.com import Channel, SocketType


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
            socket = Channel(SocketType.PUBLISH, self.port)
            eq_(socket.url, "tcp://%s:%d" % (self.hostname, self.port))

    def test_socket(self):
        with patch.object(Channel, "url_scheme", self.test_url_scheme), \
             patch.object(Channel, "url_wildcard", self.test_url_wildcard), \
             patch.object(Channel, "_bind_socket", _test_bind):
            req_socket = Channel(SocketType.REQUEST, 1)
            rep_socket = Channel(SocketType.REPLY, 0)
            value = Id("name", 1)
            req_socket.send(value)
            eq_(rep_socket.recv(), value)

if __name__ == "__main__":
    import nose
    nose.main()
