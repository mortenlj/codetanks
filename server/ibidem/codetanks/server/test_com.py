#!/usr/bin/env python
# -*- coding: utf-8

from mock import patch
from nose.tools import eq_
import zmq.green as zmq

from ibidem.codetanks.domain.ttypes import Id
from ibidem.codetanks.server.com import _Socket


class TestSocket(object):
    hostname = "test.example.com"
    port = 1234
    test_url = "inproc://socket"

    def test_has_valid_urls(self):
        with patch("ibidem.codetanks.server.com.gethostname", return_value=self.hostname):
            socket = _Socket(None, self.port)
            eq_(socket.url, "tcp://%s:%d" % (self.hostname, self.port))

    def test_socket(self):
        ctx = zmq.Context.instance()
        req = ctx.socket(zmq.REQ)
        req.bind(self.test_url)
        req_socket = _Socket(req, self.port)
        rep = ctx.socket(zmq.REP)
        rep.connect(self.test_url)
        rep_socket = _Socket(rep, self.port)
        value = Id("name", 1)
        req_socket.send(value)
        eq_(rep_socket.recv(), value)

if __name__ == "__main__":
    import nose
    nose.main()
