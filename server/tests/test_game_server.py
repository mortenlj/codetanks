#!/usr/bin/env python
# -*- coding: utf-8

from mock import create_autospec
from nose.tools import assert_is_not_none, assert_equal, assert_in

from ibidem.codetanks.domain.ttypes import Registration, GameData, ClientType, Id, RegistrationReply
from ibidem.codetanks.server.com import Channel
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.world import World


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
        self.server = GameServer(self.registration_channel, self.viewer_channel, lambda x: create_autospec(Channel(x)), create_autospec(World))
        self.server.start()


class RegistrationSetup(Shared):
    client_type = None
    client_id = None

    def setup(self):
        super(RegistrationSetup, self).setup()
        self.send_on_mock_channel(self.registration_channel, Registration(self.client_type, self.client_id))

    def send_on_mock_channel(self, channel, value):
        channel.ready.return_value = True
        channel.recv.return_value = value

    def reset_mock_channel(self, channel):
        channel.ready.return_value = None


class TestViewerRegistration(RegistrationSetup):
    client_type = ClientType.VIEWER
    client_id = Id("viewer", 1)

    def test_registering_viewer_gets_generic_urls_and_game_info(self):
        self.server._run_once()
        self.registration_channel.send.assert_called_once_with(
            RegistrationReply(self.server.build_game_info(), self.server._viewer_channel.url)
        )


class TestBotRegistration(RegistrationSetup):
    client_type = ClientType.BOT
    client_id = Id("bot", 1)

    def test_registering_bots_are_associated_with_channels(self):
        self.server._run_once()
        bot = self.server._bots[0]
        assert_is_not_none(bot)
        assert_is_not_none(bot.event_channel)
        assert_is_not_none(bot.cmd_channel)
        assert_equal(bot.tank_id, 0)

    def test_registering_bots_get_dedicated_channel_urls_and_game_info(self):
        self.server._run_once()
        bot = self.server._bots[0]
        self.registration_channel.send.assert_called_once_with(
            RegistrationReply(self.server.build_game_info(), bot.event_channel.url, bot.cmd_channel.url)
        )

    def test_bot_cmd_channel_is_polled(self):
        self.server._run_once()
        self.reset_mock_channel(self.registration_channel)
        self.server._run_once()
        bot = self.server._bots[0]
        bot.cmd_channel.ready.assert_called_once_with()

    def test_bot_is_added_to_world(self):
        self.server._run_once()
        bot = self.server._bots[0]
        self.server._world.add_tank.assert_called_once_with(bot)


class TestGameData(Shared):
    def test_game_data_sent_once_per_loop(self):
        self.server._run_once()
        def argument_matcher(data):
            return isinstance(data, GameData)
        self.viewer_channel.send.assert_called_with(_TestMatcher(argument_matcher))


if __name__ == "__main__":
    import nose
    nose.main()

