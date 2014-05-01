#!/usr/bin/env python
# -*- coding: utf-8

from mock import create_autospec, patch, call
from nose.tools import eq_
from hamcrest import assert_that, starts_with
import zmq.green as zmq
from goless.channels import GoChannel

from ibidem.codetanks.server.broker import Broker


class Shared(object):
    # Constants
    port = 1234
    hostname = "test.com"

    # Mocks
    zmq_context = None
    zmq_poller = None
    game_server_channel = None

    def setup(self):
        self.zmq_context = create_autospec(zmq.Context, instance=True)
        self.zmq_poller = create_autospec(zmq.Poller, instance=True)
        self.game_server_channel = create_autospec(GoChannel, instance=True)


class TestSockets(Shared):
    def test_are_opened(self):
        Broker(self.zmq_context, self.zmq_poller, self.game_server_channel)
        expected_calls = [call(zmq.REP), call(zmq.PUB)]
        eq_(self.zmq_context.socket.call_args_list, expected_calls)

    def test_registration_is_opened_on_given_port(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.port)
        eq_(broker.registration_socket.port, self.port)

    def test_has_valid_urls(self):
        with patch("ibidem.codetanks.server.broker.gethostname", return_value=self.hostname):
            broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.port)
            eq_(broker.registration_socket.url, "tcp://%s:%d" % (self.hostname, self.port))
            assert_that(broker.update_socket.url, starts_with("tcp://%s" % self.hostname))

    def test_are_registered_with_poller(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel)
        expected_calls = [call(broker.registration_socket), call(broker.update_socket)]
        eq_(self.zmq_poller.register.call_args_list, expected_calls)


class TestRegistration(Shared):
    viewer_registration = {"id": "viewer_id", "type": "viewer"}
    bot_registration = {"id": "bot_id", "type": "bot"}

    def test_client_gets_update_url_back(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel)
        self.zmq_poller.poll.return_value = [(broker.registration_socket.zmq_socket, zmq.POLLIN)]
        broker._run_once()
        broker.registration_socket.zmq_socket.send_json.assert_called_once_with({"update_url": broker.update_socket.url})

    def test_viewer_registration_is_forwarded_to_game_server(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel)
        self.zmq_poller.poll.return_value = [(broker.registration_socket.zmq_socket, zmq.POLLIN)]
        broker.registration_socket.zmq_socket.recv_json.return_value = self.viewer_registration
        broker._run_once()
        self.game_server_channel.send.assert_called_once_with({
            "event": "registration",
            "id": "viewer_id",
            "type": "viewer"
        })

    def test_bot_registration_is_forwarded_to_game_server(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel)
        self.zmq_poller.poll.return_value = [(broker.registration_socket.zmq_socket, zmq.POLLIN)]
        broker.registration_socket.zmq_socket.recv_json.return_value = self.bot_registration
        broker._run_once()
        self.game_server_channel.send.assert_called_once_with({
            "event": "registration",
            "id": "bot_id",
            "type": "bot"
        })


if __name__ == "__main__":
    import nose
    nose.main()
