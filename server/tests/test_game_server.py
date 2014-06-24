#!/usr/bin/env python
# -*- coding: utf-8

from mock import create_autospec
from nose.tools import assert_is_not_none, assert_equal, assert_in

from ibidem.codetanks.domain.ttypes import Registration, GameData, ClientType, Id
from ibidem.codetanks.server.com import Channel, ChannelType
from ibidem.codetanks.server.game_server import GameServer


class _TestMatcher(object):
    def __init__(self, test):
        self._test = test

    def __eq__(self, other):
        return self._test(other)


def assert_arguments_matches(call_args, *matchers):
    args, kwargs = call_args
    assert_equal(args, matchers)


def assert_has_key(d, key):
    assert_in(key, d.keys(), "The key %r was not found in %r" % (key, d.keys()))


class Shared(object):
    def setup(self):
        self.registration_channel = create_autospec(Channel)
        self.registration_channel.ready.return_value = False
        self.viewer_channel = create_autospec(Channel)
        self.server = GameServer(self.registration_channel, self.viewer_channel, lambda x: create_autospec(Channel(x)))
        self.server.start()

    def send_on_mock_channel(self, channel, value):
        channel.ready.return_value = True
        channel.recv.return_value = value


class TestBounds(Shared):
    def test_server_has_bounds(self):
        assert_is_not_none(self.server.bounds)

    def test_server_bounds_are_valid(self):
        assert_equal(self.server.bounds.left, 0)
        assert_equal(self.server.bounds.width, 500)
        assert_equal(self.server.bounds.top, 0)
        assert_equal(self.server.bounds.height, 500)

    def test_server_returns_bounds_in_info(self):
        game_info = self.server.build_game_info()
        arena = game_info.arena
        assert_equal(arena.height, self.server.bounds.height)
        assert_equal(arena.width, self.server.bounds.width)


class TestRegistration(Shared):
    def _registration_triggers_sending_game_info(self, type, id):
        self.send_on_mock_channel(self.registration_channel, Registration(type, id))
        self.server._run_once()
        assert_arguments_matches(self.viewer_channel.send.call_args_list[0], self.server.build_game_info())

    def test_registration_triggers_sending_game_info(self):
        for id, type in (
                (ClientType.VIEWER, Id("viewer", 1)),
                (ClientType.BOT, Id("bot", 1))
            ):
            yield self._registration_triggers_sending_game_info, id, type

    def test_registering_bots_are_associated_with_channels(self):
        bot_id = Id("bot", 1)
        self.send_on_mock_channel(self.registration_channel, Registration(ClientType.BOT, bot_id))
        self.server._run_once()
        assert_has_key(self.server._bot_channels, bot_id)
        assert_has_key(self.server._bot_channels[bot_id], ChannelType.PUBLISH)
        assert_has_key(self.server._bot_channels[bot_id], ChannelType.REPLY)


class TestGameData(Shared):
    def test_game_data_sent_once_per_loop(self):
        self.server._run_once()
        def argument_matcher(data):
            return isinstance(data, GameData)
        self.viewer_channel.send.assert_called_with(_TestMatcher(argument_matcher))

    def test_game_data_is_initialized_with_lists(self):
        self.server._run_once()
        def argument_matcher(data):
            return isinstance(data.bullets, list) and isinstance(data.tanks, list)
        self.viewer_channel.send.assert_called_with(_TestMatcher(argument_matcher))


if __name__ == "__main__":
    import nose
    nose.main()

