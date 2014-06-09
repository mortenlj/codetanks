#!/usr/bin/env python
# -*- coding: utf-8

from mock import create_autospec, call
from nose.tools import eq_
import zmq.green as zmq
from goless.channels import GoChannel

from ibidem.codetanks.domain.ttypes import Registration, RegistrationReply, GameInfo, Arena, ClientType, Id
from ibidem.codetanks.domain.util import serialize
from ibidem.codetanks.server.broker import Broker


class MockFrame(object):
    def __init__(self, buffer):
        self.buffer = buffer


class Shared(object):
    port = 1234

    # Mocks
    zmq_context = None
    zmq_poller = None
    game_server_channel = None
    viewer_channel = None

    def setup(self):
        self.zmq_context = create_autospec(zmq.Context, instance=True)
        self.zmq_poller = create_autospec(zmq.Poller, instance=True)
        self.game_server_channel = create_autospec(GoChannel, instance=True)
        self.viewer_channel = create_autospec(GoChannel, instance=True)
        self.viewer_channel.recv_ready.return_value = False


class TestSockets(Shared):
    hostname = "test.com"

    def test_are_opened(self):
        Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.viewer_channel, self.port)
        expected_calls = [call(zmq.REP), call(zmq.PUB)]
        eq_(self.zmq_context.socket.call_args_list, expected_calls)

    def test_registration_is_opened_on_given_port(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.viewer_channel, self.port)
        eq_(broker.registration_socket.port, self.port)

    def test_are_registered_with_poller(self):
        broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.viewer_channel, self.port)
        expected_calls = [call(broker.registration_socket.zmq_socket), call(broker.viewer_socket.zmq_socket)]
        eq_(self.zmq_poller.register.call_args_list, expected_calls)


class TestRegistration(Shared):
    viewer_registration = Registration(ClientType.VIEWER, Id("viewer_id", 1))
    bot_registration = Registration(ClientType.BOT, Id("bot_id", 1))

    def setup(self):
        super(TestRegistration, self).setup()
        self.broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.viewer_channel, self.port)

    def test_client_gets_update_url_back(self):
        self.zmq_poller.poll.return_value = [(self.broker.registration_socket.zmq_socket, zmq.POLLIN)]
        self.broker.registration_socket.zmq_socket.recv.return_value = MockFrame(serialize(self.bot_registration))
        self.broker._run_once()
        serialized_reply = serialize(RegistrationReply(self.broker.viewer_socket.url))
        self.broker.registration_socket.zmq_socket.send.assert_called_once_with(serialized_reply, copy=False)

    def test_viewer_registration_is_forwarded_to_game_server(self):
        self.zmq_poller.poll.return_value = [(self.broker.registration_socket.zmq_socket, zmq.POLLIN)]
        self.broker.registration_socket.zmq_socket.recv.return_value = MockFrame(serialize(self.viewer_registration))
        self.broker._run_once()
        self.game_server_channel.send.assert_called_once_with(self.viewer_registration)

    def test_bot_registration_is_forwarded_to_game_server(self):
        self.zmq_poller.poll.return_value = [(self.broker.registration_socket.zmq_socket, zmq.POLLIN)]
        self.broker.registration_socket.zmq_socket.recv.return_value = MockFrame(serialize(self.bot_registration))
        self.broker._run_once()
        self.game_server_channel.send.assert_called_once_with(self.bot_registration)


class TestChannels(Shared):
    update_message = GameInfo(Arena(10, 90))

    def setup(self):
        super(TestChannels, self).setup()
        self.broker = Broker(self.zmq_context, self.zmq_poller, self.game_server_channel, self.viewer_channel, self.port)

    def test_forwards_messages_on_viewer_socket(self):
        values = [True, False]
        def return_value(*args):
            if len(values) > 1:
                return values.pop(0)
            return values[0]
        self.broker.viewer_channel.recv_ready.side_effect = return_value
        self.broker.viewer_channel.recv.return_value = self.update_message
        self.broker._run_once()
        self.broker.viewer_socket.zmq_socket.send.assert_called_once_with(serialize(self.update_message), copy=False)


if __name__ == "__main__":
    import nose
    nose.main()
