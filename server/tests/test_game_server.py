#!/usr/bin/env python
# -*- coding: utf-8
from datetime import datetime, timedelta

import pytest
from mock import create_autospec, MagicMock, PropertyMock

from ibidem.codetanks.domain.messages_pb2 import Registration, GameData, ClientType, Id, RegistrationReply, Command, \
    CommandType, CommandReply, \
    CommandResult, BotStatus, ScanResult, Tank, Death, GameInfo, RegistrationResult, Event, Arena, Point
from ibidem.codetanks.server.com import Channel
from ibidem.codetanks.server.constants import PLAYER_COUNT, MAX_HEALTH, BULLET_DAMAGE, TANK_SPEED, ROTATION, \
    BULLET_SPEED, TANK_RADIUS, BULLET_RADIUS
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.vehicle import Armour
from ibidem.codetanks.server.world import World

VICTORY_DELAY = timedelta(seconds=1)
BOT_CLIENT_ID = Id(name="bot", version=1)


@pytest.fixture
def registration_channel():
    registration_channel = create_autospec(Channel)
    registration_channel.url = "tcp://registration_channel.url"
    registration_channel.ready.return_value = False
    return registration_channel


@pytest.fixture
def viewer_channel():
    viewer_channel = create_autospec(Channel)
    viewer_channel.url = "tcp://viewer_channel.url"
    return viewer_channel


@pytest.fixture
def world():
    world = create_autospec(World)
    world.arena = Arena()
    world.gamedata = GameData()
    return world


@pytest.fixture
def server(registration_channel, viewer_channel, world):
    def channel_factory(x):
        mock = create_autospec(Channel, instance=True)
        mock.ready.return_value = False
        mock.url = "tcp://mock_channel.url"
        return mock

    return GameServer(registration_channel, viewer_channel, channel_factory, world, VICTORY_DELAY)


def send_on_mock_channel(channel, value):
    channel.ready.return_value = True
    channel.recv.return_value = value


def reset_mock_channel(channel):
    channel.ready.return_value = None


class TestViewerRegistration:
    @pytest.fixture(autouse=True)
    def send_registration(self, registration_channel):
        send_on_mock_channel(registration_channel,
                             Registration(client_type=ClientType.VIEWER, id=Id(name="viewer", version=1)))

    def test_registering_viewer_gets_generic_urls_and_game_info(self, server, registration_channel):
        server._run_once()
        registration_channel.send.assert_called_once_with(
            RegistrationReply(result=RegistrationResult.SUCCESS,
                              game_info=server.build_game_info(),
                              event_url=server._viewer_channel.url)
        )


class TestBotRegistration:
    @pytest.fixture(autouse=True)
    def send_registration(self, registration_channel):
        send_on_mock_channel(registration_channel, Registration(client_type=ClientType.BOT, id=BOT_CLIENT_ID))

    def test_registering_bots_are_associated_with_channels(self, server):
        server._run_once()
        bot = server._bots[0]
        assert bot is not None
        assert bot.event_channel is not None
        assert bot.cmd_channel is not None
        assert bot.tank_id == 0

    def test_registering_bots_get_dedicated_channel_urls_and_game_info(self, server, registration_channel):
        server._run_once()
        bot = server._bots[0]
        registration_channel.send.assert_called_once_with(
            RegistrationReply(result=RegistrationResult.SUCCESS,
                              game_info=server.build_game_info(),
                              event_url=bot.event_channel.url,
                              cmd_url=bot.cmd_channel.url,
                              id=0)
        )

    def test_bot_cmd_channel_is_polled(self, server, registration_channel):
        server._run_once()
        reset_mock_channel(registration_channel)
        server._run_once()
        bot = server._bots[0]
        bot.cmd_channel.ready.assert_called_once_with()

    def test_bot_is_added_to_world(self, server, world):
        server._run_once()
        world.add_tank.assert_called_once_with(BOT_CLIENT_ID, 0)


class TestGame:
    @pytest.fixture
    def server(self, server):
        server._handle_bot_registration(Registration(client_type=ClientType.BOT, id=Id(name="bot", version=1)))
        return server

    @pytest.fixture
    def bot(self, server):
        bot = server._bots[0]
        bot.tank.status = BotStatus.IDLE
        bot.tank.position = Point(x=1, y=1)
        bot.tank.direction = Point(x=1, y=0)
        bot.tank.turret = Point(x=0, y=1)
        return bot

    def test_game_data_sent_once_per_loop(self, server, world, viewer_channel):
        game_data = GameData(bullets=[], tanks=[])
        type(world).gamedata = PropertyMock(return_value=game_data)
        server._run_once()
        viewer_channel.send.assert_called_with(Event(game_data=game_data))

    def test_events_gathered_once_per_loop(self, server, world):
        world.get_events.return_value = {}
        server._run_once()
        world.get_events.assert_called_once_with()

    def test_events_sent_when_gathered(self, server, world, bot):
        scan_result = Event(scan=ScanResult(tanks=[]))
        world.get_events.return_value = {bot.tank_id: [scan_result]}
        server._run_once()
        bot.event_channel.send.assert_called_once_with(scan_result)

    def test_events_sent_to_all_when_no_tank_id(self, server, world, bot):
        death = Event(death=Death(victim=Tank(), perpetrator=Tank()))
        world.get_events.return_value = {None: [death]}
        server._run_once()
        bot.event_channel.send.assert_called_once_with(death)

    def test_bot_command_receives_reply(self, server, bot):
        send_on_mock_channel(bot.cmd_channel, Command(type=CommandType.MOVE, value=10))
        server._run_once()
        bot.cmd_channel.send.assert_called_once_with(CommandReply(result=CommandResult.ACCEPTED))

    @pytest.mark.parametrize("command, name, param", (
            (Command(type=CommandType.MOVE, value=10), "move", 10),
            (Command(type=CommandType.ROTATE, value=10), "rotate", 10),
            (Command(type=CommandType.AIM, value=10), "aim", 10),
            (Command(type=CommandType.SCAN, value=10), "scan", 10),
            (Command(type=CommandType.FIRE), "fire", None),
            (Command(type=CommandType.MOVE, value=0), "move", 0),
            (Command(type=CommandType.ROTATE, value=0), "rotate", 0),
            (Command(type=CommandType.AIM, value=0), "aim", 0),
            (Command(type=CommandType.SCAN, value=0), "scan", 0),
    ))
    def test_command(self, server, bot, command, name, param):
        send_on_mock_channel(bot.cmd_channel, command)
        server._run_once()
        if param is None:
            getattr(bot.tank, name).assert_called_once_with()
        else:
            getattr(bot.tank, name).assert_called_once_with(param)

    @pytest.fixture(params=(s for s in BotStatus.values() if s != BotStatus.IDLE))
    def command_abort_if_busy_states(self, request):
        yield request.param

    @pytest.mark.parametrize("command", (
            Command(type=CommandType.MOVE, value=10),
            Command(type=CommandType.ROTATE, value=1),
            Command(type=CommandType.AIM, value=-1)
    ))
    def test_command_abort_if_busy(self, server, bot, command_abort_if_busy_states, command):
        bot.tank.status = command_abort_if_busy_states
        send_on_mock_channel(bot.cmd_channel, command)
        server._run_once()
        getattr(bot.tank, CommandType.Name(command.type).lower()).assert_not_called()
        bot.cmd_channel.send.assert_called_once_with(CommandReply(result=CommandResult.BUSY))

    def test_game_started_after_fourth_bot(self, server, world, bot):
        world.add_tank.return_value = Armour(Tank(), world)
        bot.tank = Armour(Tank(), world)
        # One from fixture, and another three here
        for i in range(PLAYER_COUNT - 1):
            assert not server.started()
            server._handle_bot_registration(Registration(client_type=ClientType.BOT, id=Id(name="bot", version=1)))
        assert server.started()

    def test_update_not_called_before_game_started(self, server, world):
        server._run_once()
        world.update.assert_not_called()

    def test_game_does_not_end_when_only_one_bot_registered(self, server, world):
        world.number_of_live_bots = 1
        assert not server.finished()


class TestStartedGame:
    @pytest.fixture
    def server(self, server, world):
        world.add_tank.return_value = Armour(Tank(), world)
        for i in range(PLAYER_COUNT):
            server._handle_bot_registration(Registration(client_type=ClientType.BOT, id=Id(name="bot", version=1)))
        return server

    @pytest.fixture
    def world(self, world):
        world.number_of_live_bots = PLAYER_COUNT
        world.gamedata = GameData()
        return world

    def test_world_updated_once_per_loop(self, server, world):
        server.clock = MagicMock()
        server.clock.tick.return_value = 30
        server._run_once()
        world.update.assert_called_once_with(30)

    def test_game_ends_when_only_one_bot_left(self, server, world):
        world.number_of_live_bots = 1
        assert server.finished()

    def test_game_ends_when_all_bots_are_dead(self, server, world):
        world.number_of_live_bots = 0
        assert server.finished()

    def test_loop_ends_after_victory_delay_when_finished(self, server, world):
        world.number_of_live_bots = 1
        world.get_live_bots.return_value = [Armour(Tank(), world)]
        start = datetime.now()
        server.run()
        end = datetime.now()
        assert (end - start).total_seconds() == pytest.approx(VICTORY_DELAY.total_seconds(), abs=0.1)

    def test_new_bots_are_refused_when_game_started(self, server, world, registration_channel):
        server._handle_bot_registration(Registration(client_type=ClientType.BOT, id=Id(name="bot", version=1)))
        game_info = GameInfo(
            arena=world.arena,
            max_health=MAX_HEALTH,
            bullet_damage=BULLET_DAMAGE,
            player_count=PLAYER_COUNT,
            tank_speed=TANK_SPEED,
            rotation=ROTATION,
            bullet_speed=BULLET_SPEED,
            tank_radius=TANK_RADIUS,
            bullet_radius=BULLET_RADIUS
        )
        registration_channel.send.assert_called_with(
            RegistrationReply(result=RegistrationResult.FAILURE, game_info=game_info))
