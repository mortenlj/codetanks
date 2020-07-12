#!/usr/bin/env python
# -*- coding: utf-8
from datetime import datetime, timedelta

import pytest
from mock import create_autospec, MagicMock, PropertyMock

from ibidem.codetanks.domain.ttypes import Registration, GameData, ClientType, Id, RegistrationReply, Command, \
    CommandType, CommandReply, \
    CommandResult, BotStatus, ScanResult, Tank, Death, GameInfo, RegistrationResult, Event
from ibidem.codetanks.server.com import Channel
from ibidem.codetanks.server.constants import PLAYER_COUNT, MAX_HEALTH, BULLET_DAMAGE, TANK_SPEED, ROTATION, \
    BULLET_SPEED, TANK_RADIUS, BULLET_RADIUS
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.world import World


class Shared(object):
    def setup(self):
        self.registration_channel = create_autospec(Channel)
        self.registration_channel.ready.return_value = False
        self.viewer_channel = create_autospec(Channel)

        def channel_factory(x):
            mock = create_autospec(Channel, instance=True)
            mock.ready.return_value = False
            return mock

        self.world = create_autospec(World)
        self.victory_delay = timedelta(seconds=1)
        self.server = GameServer(self.registration_channel,
                                 self.viewer_channel,
                                 channel_factory,
                                 self.world,
                                 self.victory_delay)

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
            RegistrationReply(RegistrationResult.SUCCESS, self.server.build_game_info(),
                              self.server._viewer_channel.url)
        )


class TestBotRegistration(RegistrationSetup):
    client_type = ClientType.BOT
    client_id = Id("bot", 1)

    def test_registering_bots_are_associated_with_channels(self):
        self.server._run_once()
        bot = self.server._bots[0]
        assert bot is not None
        assert bot.event_channel is not None
        assert bot.cmd_channel is not None
        assert bot.tank_id == 0

    def test_registering_bots_get_dedicated_channel_urls_and_game_info(self):
        self.server._run_once()
        bot = self.server._bots[0]
        self.registration_channel.send.assert_called_once_with(
            RegistrationReply(RegistrationResult.SUCCESS, self.server.build_game_info(), bot.event_channel.url,
                              bot.cmd_channel.url, 0)
        )

    def test_bot_cmd_channel_is_polled(self):
        self.server._run_once()
        self.reset_mock_channel(self.registration_channel)
        self.server._run_once()
        bot = self.server._bots[0]
        bot.cmd_channel.ready.assert_called_once_with()

    def test_bot_is_added_to_world(self):
        self.server._run_once()
        self.world.add_tank.assert_called_once_with(self.client_id, 0)


class TestGame(Shared):
    def setup(self):
        super(TestGame, self).setup()
        self.server._handle_bot_registration(Registration(ClientType.BOT, Id("bot", 1)))
        self.bot = self.server._bots[0]
        self.bot._tank.status = BotStatus.IDLE

    def test_game_data_sent_once_per_loop(self):
        game_data = GameData([], [])
        type(self.world).gamedata = PropertyMock(return_value=game_data)
        self.server._run_once()
        self.viewer_channel.send.assert_called_with(game_data)

    def test_events_gathered_once_per_loop(self):
        self.world.get_events.return_value = {}
        self.server._run_once()
        self.world.get_events.assert_called_once_with()

    def test_events_sent_when_gathered(self):
        scan_result = Event(scan=ScanResult([]))
        self.world.get_events.return_value = {self.bot.tank_id: [scan_result]}
        self.server._run_once()
        self.bot.event_channel.send.assert_called_once_with(scan_result)

    def test_events_sent_to_all_when_no_tank_id(self):
        death = Event(death=Death(create_autospec(Tank), create_autospec(Tank)))
        self.world.get_events.return_value = {None: [death]}
        self.server._run_once()
        self.bot.event_channel.send.assert_called_once_with(death)

    def test_bot_command_receives_reply(self):
        self.send_on_mock_channel(self.bot.cmd_channel, Command(CommandType.MOVE, 10))
        self.server._run_once()
        self.bot.cmd_channel.send.assert_called_once_with(CommandReply(CommandResult.OK))

    @pytest.mark.parametrize("command, name, param", (
            (Command(CommandType.MOVE, 10), "move", 10),
            (Command(CommandType.ROTATE, 10), "rotate", 10),
            (Command(CommandType.AIM, 10), "aim", 10),
            (Command(CommandType.SCAN, 10), "scan", 10),
            (Command(CommandType.FIRE), "fire", None),
            (Command(CommandType.MOVE, 0), "move", 0),
            (Command(CommandType.ROTATE, 0), "rotate", 0),
            (Command(CommandType.AIM, 0), "aim", 0),
            (Command(CommandType.SCAN, 0), "scan", 0),
    ))
    def test_command(self, command, name, param):
        self.send_on_mock_channel(self.bot.cmd_channel, command)
        self.server._run_once()
        if param is None:
            getattr(self.bot._tank, name).assert_called_once_with()
        else:
            getattr(self.bot._tank, name).assert_called_once_with(param)

    @pytest.fixture(params=(s for s in BotStatus._NAMES_TO_VALUES.values() if s != BotStatus.IDLE))
    def command_abort_if_busy_states(self, request):
        yield request.param

    @pytest.mark.parametrize("command", (
            Command(CommandType.MOVE, 10),
            Command(CommandType.ROTATE, 1.5),
            Command(CommandType.AIM, -1.5)
    ))
    def test_command_abort_if_busy(self, command_abort_if_busy_states, command):
        self.bot._tank.status = command_abort_if_busy_states
        self.send_on_mock_channel(self.bot.cmd_channel, command)
        self.server._run_once()
        getattr(self.bot._tank, CommandType._VALUES_TO_NAMES[command.type]).assert_not_called()
        self.bot.cmd_channel.send.assert_called_once_with(CommandReply(CommandResult.BUSY))

    def test_game_started_after_fourth_bot(self):
        # One from setup, and another three here
        for i in range(PLAYER_COUNT - 1):
            assert not self.server.started()
            self.server._handle_bot_registration(Registration(ClientType.BOT, Id("bot", 1)))
        assert self.server.started()

    def test_update_not_called_before_game_started(self):
        self.server._run_once()
        self.world.update.assert_not_called()

    def test_game_does_not_end_when_only_one_bot_registered(self):
        self.world.number_of_live_bots = 1
        assert not self.server.finished()


class TestStartedGame(Shared):
    def setup(self):
        super(TestStartedGame, self).setup()
        for i in range(PLAYER_COUNT):
            self.server._handle_bot_registration(Registration(ClientType.BOT, Id("bot", 1)))
        self.world.number_of_live_bots = PLAYER_COUNT

    def test_world_updated_once_per_loop(self):
        self.server.clock = MagicMock()
        self.server.clock.tick.return_value = 30
        self.server._run_once()
        self.world.update.assert_called_once_with(30)

    def test_game_ends_when_only_one_bot_left(self):
        self.world.number_of_live_bots = 1
        assert self.server.finished()

    def test_game_ends_when_all_bots_are_dead(self):
        self.world.number_of_live_bots = 0
        assert self.server.finished()

    def test_loop_ends_after_victory_delay_when_finished(self):
        self.world.number_of_live_bots = 1
        start = datetime.now()
        self.server.run()
        end = datetime.now()
        assert (end - start).total_seconds() == pytest.approx(self.victory_delay.total_seconds(), abs=0.1)

    def test_new_bots_are_refused_when_game_started(self):
        self.server._handle_bot_registration(Registration(ClientType.BOT, Id("bot", 1)))
        game_info = GameInfo(
            self.world.arena,
            MAX_HEALTH,
            BULLET_DAMAGE,
            PLAYER_COUNT,
            TANK_SPEED,
            ROTATION,
            BULLET_SPEED,
            TANK_RADIUS,
            BULLET_RADIUS
        )
        self.registration_channel.send.assert_called_with(
            RegistrationReply(RegistrationResult.FAILURE, game_info))
