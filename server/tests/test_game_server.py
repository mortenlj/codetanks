#!/usr/bin/env python
# -*- coding: utf-8
from datetime import datetime, timedelta

import pytest
from ibidem.codetanks.domain.messages_pb2 import GameData, ClientType, Id, RegistrationReply, Command, \
    CommandType, CommandReply, \
    CommandResult, BotStatus, Tank, Death, GameInfo, RegistrationResult, Event, Arena, Point, ScanComplete
from mock import create_autospec, MagicMock, PropertyMock

from ibidem.codetanks.server import peer
from ibidem.codetanks.server.constants import PLAYER_COUNT, MAX_HEALTH, BULLET_DAMAGE, TANK_SPEED, ROTATION, \
    BULLET_SPEED, TANK_RADIUS, BULLET_RADIUS, CANNON_RELOAD
from ibidem.codetanks.server.game_server import GameServer
from ibidem.codetanks.server.vehicle import Armour
from ibidem.codetanks.server.world import World

VICTORY_DELAY = timedelta(seconds=1)
BOT_CLIENT_ID = Id(name="bot", version=1)


@pytest.fixture
def world():
    world = create_autospec(World)
    world.arena = Arena()
    world.gamedata = GameData()
    return world


@pytest.fixture
def server(world):
    return GameServer(world, VICTORY_DELAY)


def _make_peer(client_type, id):
    m = MagicMock(peer.Peer, instance=True)
    m.client_type = client_type
    m.id = id
    return m


@pytest.fixture
def bot_peer():
    return _make_peer(ClientType.BOT, BOT_CLIENT_ID)


@pytest.fixture
def viewer_peer():
    return _make_peer(ClientType.VIEWER, Id(name="viewer", version=1))


class TestViewerRegistration:
    def test_registering_viewer_gets_game_info(self, server, viewer_peer):
        reply = server.add_peer(viewer_peer)
        assert reply == RegistrationReply(result=RegistrationResult.SUCCESS,
                                          game_info=server.build_game_info(),
                                          )


class TestBotRegistration:
    def test_registering_bots_are_associated_with_channels(self, server, bot_peer):
        server.add_peer(bot_peer)
        peer, bot = server._bots[0]
        assert peer is bot_peer
        assert bot is not None
        assert bot.tank_id == 0

    def test_registering_bots_get_game_info(self, server, bot_peer):
        reply = server.add_peer(bot_peer)
        assert reply == RegistrationReply(result=RegistrationResult.SUCCESS,
                                          game_info=server.build_game_info(),
                                          id=0)

    def test_bot_cmd_channel_is_polled(self, server, bot_peer):
        server.add_peer(bot_peer)
        server._run_once()
        peer, bot = server._bots[0]
        peer.next_command.assert_called_once()

    def test_bot_called_to_handle_command(self, server, bot_peer):
        cmd = Command(type=CommandType.MOVE, value=10)
        bot_peer.next_command.return_value = cmd
        server.add_peer(bot_peer)
        peer, bot = server._bots[0]
        bot.handle_command = MagicMock()
        server._run_once()
        peer.next_command.assert_called_once()
        bot.handle_command.assert_called_once_with(cmd)

    def test_bot_is_added_to_world(self, server, bot_peer, world):
        server.add_peer(bot_peer)
        world.add_tank.assert_called_once_with(BOT_CLIENT_ID, 0)


class TestGame:
    @pytest.fixture
    def server(self, server, bot_peer):
        server.add_peer(bot_peer)
        return server

    @pytest.fixture
    def bot(self, server):
        _peer, bot = server._bots[0]
        bot.tank.status = BotStatus.IDLE
        bot.tank.position = Point(x=1, y=1)
        bot.tank.direction = Point(x=1, y=0)
        bot.tank.turret = Point(x=0, y=1)
        return bot

    def test_game_data_sent_once_per_loop(self, server, world, viewer_peer):
        server.add_peer(viewer_peer)
        game_data = GameData(bullets=[], tanks=[])
        type(world).gamedata = PropertyMock(return_value=game_data)
        server._run_once()
        viewer_peer.handle_event.assert_called_with(Event(game_data=game_data))

    def test_events_gathered_once_per_loop(self, server, world):
        world.get_events.return_value = {}
        server._run_once()
        world.get_events.assert_called_once_with()

    def test_events_sent_when_gathered(self, server, world, bot, bot_peer):
        scan_result = Event(scan_complete=ScanComplete(tanks=[]))
        world.get_events.return_value = {bot.tank_id: [scan_result]}
        server._run_once()
        bot_peer.handle_event.assert_called_once_with(scan_result)

    def test_events_sent_to_all_when_no_tank_id(self, server, world, bot, bot_peer):
        death = Event(death=Death(victim=Tank(), perpetrator=Tank()))
        world.get_events.return_value = {None: [death]}
        server._run_once()
        bot_peer.handle_event.assert_called_once_with(death)

    def test_bot_command_receives_reply(self, server, bot, bot_peer):
        bot_peer.next_command.return_value = Command(type=CommandType.MOVE, value=10)
        server._run_once()
        bot_peer.command_reply.assert_called_once_with(CommandReply(result=CommandResult.ACCEPTED))

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
    def test_command(self, server, bot, bot_peer, command, name, param):
        bot_peer.next_command.return_value = command
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
    def test_command_abort_if_busy(self, server, bot, bot_peer, command_abort_if_busy_states, command):
        bot.tank.status = command_abort_if_busy_states
        bot_peer.next_command.return_value = command
        server._run_once()
        getattr(bot.tank, CommandType.Name(command.type).lower()).assert_not_called()
        bot_peer.command_reply.assert_called_once_with(CommandReply(result=CommandResult.BUSY))

    def test_game_full_after_fourth_bot(self, server, world, bot):
        world.add_tank.return_value = Armour(Tank(), world)
        bot.tank = Armour(Tank(), world)
        # One from fixture, and another three here
        for i in range(PLAYER_COUNT - 1):
            assert not server.started()
            server.add_peer(_make_peer(ClientType.BOT, Id(name="bot", version=1)))
        assert server.game_full()

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
            server.add_peer(_make_peer(ClientType.BOT, Id(name="bot", version=1)))
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
        assert (end - start).total_seconds() == pytest.approx(VICTORY_DELAY.total_seconds(), abs=0.2)

    def test_new_bots_are_refused_when_game_started(self, server, world):
        reply = server.add_peer(_make_peer(ClientType.BOT, Id(name="bot", version=1)))
        game_info = GameInfo(
            arena=world.arena,
            max_health=MAX_HEALTH,
            bullet_damage=BULLET_DAMAGE,
            player_count=PLAYER_COUNT,
            tank_speed=TANK_SPEED,
            rotation=ROTATION,
            bullet_speed=BULLET_SPEED,
            tank_radius=TANK_RADIUS,
            bullet_radius=BULLET_RADIUS,
            cannon_reload=CANNON_RELOAD,
        )
        assert reply == RegistrationReply(result=RegistrationResult.FAILURE, game_info=game_info)

    def test_new_viewers_are_accepted_when_game_started(self, server, world):
        reply = server.add_peer(_make_peer(ClientType.VIEWER, Id(name="viewer", version=1)))
        game_info = GameInfo(
            arena=world.arena,
            max_health=MAX_HEALTH,
            bullet_damage=BULLET_DAMAGE,
            player_count=PLAYER_COUNT,
            tank_speed=TANK_SPEED,
            rotation=ROTATION,
            bullet_speed=BULLET_SPEED,
            tank_radius=TANK_RADIUS,
            bullet_radius=BULLET_RADIUS,
            cannon_reload=CANNON_RELOAD,
        )
        assert reply == RegistrationReply(result=RegistrationResult.SUCCESS, game_info=game_info)
