#!/usr/bin/env python
# -*- coding: utf-8

from mock import create_autospec, patch, call
from nose.tools import eq_, assert_true
import zmq

from ibidem.codetanks.server.broker import Broker


class Shared(object):
    # Constants
    port = 1234
    hostname = "test.com"

    # Mocks
    zmq_context = None
    zmq_poller = None

    def setup(self):
        self.zmq_context = create_autospec(zmq.Context)
        self.zmq_poller = create_autospec(zmq.Poller, instance=True)


class TestSockets(Shared):
    def test_are_opened(self):
        Broker(self.zmq_context, self.zmq_poller)
        expected_calls = [call(zmq.REP), call(zmq.PUB)]
        eq_(self.zmq_context.socket.call_args_list, expected_calls)

    def test_registration_is_opened_on_given_port(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.port)
        eq_(broker.registration_socket.port, self.port)

    def test_has_valid_urls(self):
        with patch("ibidem.codetanks.server.broker.gethostname", return_value=self.hostname):
            broker = Broker(self.zmq_context, self.zmq_poller, self.port)
            eq_(broker.registration_socket.url, "tcp://%s:%d" % (self.hostname, self.port))
            assert_true(broker.update_socket.url.startswith("tcp://%s" % self.hostname))

    def test_are_registered_with_poller(self):
        broker = Broker(self.zmq_context, self.zmq_poller)
        expected_calls = [call(broker.registration_socket), call(broker.update_socket)]
        eq_(self.zmq_poller.register.call_args_list, expected_calls)


if __name__ == "__main__":
    import nose
    nose.main()
