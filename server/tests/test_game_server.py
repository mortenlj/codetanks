#!/usr/bin/env python
# -*- coding: utf-8

from mock import create_autospec, MagicMock, PropertyMock
from nose.tools import assert_is_not_none, assert_equal
import pygame

from ibidem.codetanks.domain.ttypes import Registration, GameData, ClientType, Id, RegistrationReply, Move, CommandReply, CommandResult, \
    Rotate, BotStatus, Aim, Fire
from ibidem.codetanks.server.com import Channel
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.world import World


class Shared(object):
    def setup(self):
        self.registration_channel = create_autospec(Channel)
        self.registration_channel.ready.return_value = False
        self.viewer_channel = create_autospec(Channel)
        def channel_factory(x):
            mock = create_autospec(Channel(x))
            mock.ready.return_value = False
            return mock
        self.server = GameServer(self.registration_channel, self.viewer_channel, channel_factory, create_autospec(World))
        self.server.start()

    def send_on_mock_channel(self, channel, value):
        channel.ready.return_value = True
        channel.recv.return_value = value

    def reset_mock_channel(self, channel):
        channel.ready.return_value = None


class RegistrationSetup(Shared):
    client_type = None
    client_id = None

    def setup(self):
        super(RegistrationSetup, self).setup()
        self.send_on_mock_channel(self.registration_channel, Registration(self.client_type, self.client_id))


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


class TestGame(Shared):
    def setup(self):
        super(TestGame, self).setup()
        self.server.clock = create_autospec(pygame.time.Clock)
        self.server.clock.tick = MagicMock()
        self.server._handle_bot_registration(self.registration_channel, Registration(ClientType.BOT, Id("bot", 1)))
        self.bot = self.server._bots[0]
        self.server._world.tank_status.return_value = BotStatus.IDLE

    def test_game_data_sent_once_per_loop(self):
        game_data = GameData([], [])
        type(self.server._world).gamedata = PropertyMock(return_value=game_data)
        self.server._run_once()
        self.viewer_channel.send.assert_called_with(game_data)

    def test_world_updated_once_per_loop(self):
        self.server.clock.tick.return_value = 30
        self.server._run_once()
        self.server._world.update.assert_called_once_with(30)

    def test_bot_command_receives_reply(self):
        self.send_on_mock_channel(self.bot.cmd_channel, Move(10))
        self.server._run_once()
        self.bot.cmd_channel.send.assert_called_once_with(CommandReply(CommandResult.OK))

    def _command_test(self, command, name, *params):
        self.send_on_mock_channel(self.bot.cmd_channel, command)
        self.server._run_once()
        self.server._world.command.assert_called_once_with(self.bot.tank_id, name, *params)

    def test_commands_forwarded_to_world(self):
        yield ("_command_test", Move(10), "move", 10)
        yield ("_command_test", Rotate(10), "rotate", 10)
        yield ("_command_test", Aim(10), "aim", 10)
        yield ("_command_test", Fire(), "fire")

    def _command_abort_if_busy_test(self, status, command):
        self.server._world.tank_status.return_value = status
        self.send_on_mock_channel(self.bot.cmd_channel, command)
        self.server._run_once()
        assert_equal(self.server._world.command.called, False)
        self.bot.cmd_channel.send.assert_called_once_with(CommandReply(CommandResult.BUSY))

    def test_command_aborted_if_busy(self):
        states = list(BotStatus._NAMES_TO_VALUES.values())
        states.remove(BotStatus.IDLE)
        for status in states:
            for command in (Move(10), Rotate(1.5), Aim(-1.5)):
                yield self._command_abort_if_busy_test, status, command


if __name__ == "__main__":
    import nose
    nose.main()

