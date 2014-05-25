#!/usr/bin/env python
# -*- coding: utf-8

from goless.channels import chan
from nose.tools import assert_is_not_none, assert_equal, assert_false, assert_true, assert_is_instance

from ibidem.codetanks.domain.ttypes import Registration, GameData
from ibidem.codetanks.server.game_server import GameServer


class Shared(object):
    def setup(self):
        self.input_channel = chan(1)
        self.update_channel = chan(2)
        self.server = GameServer(self.input_channel, self.update_channel)


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


class TestState(Shared):
    def test_new_server_is_not_started(self):
        assert_false(self.server.started())

    def test_started_server_is_started(self):
        self.server.start()
        assert_true(self.server.started())


class TestRegistration(Shared):
    def _registration_triggers_sending_game_info(self, id, type):
        self.input_channel.send(Registration(type, id))
        self.server._run_once()
        assert_true(self.update_channel.recv_ready(), "Update channel is not ready to receive")
        game_info = self.update_channel.recv()
        game_info_message = self.server.build_game_info()
        assert_equal(game_info, game_info_message)

    def test_registration_triggers_sending_game_info(self):
        for id, type in (("viewer_id", "viewer"), ("bot_id", "bot")):
            yield self._registration_triggers_sending_game_info, id, type


class TestGameData(Shared):
    def test_game_data_sent_once_per_loop(self):
        self.server._run_once()
        assert_true(self.update_channel.recv_ready(), "Update channel is not ready to receive")
        game_data = self.update_channel.recv()
        assert_is_instance(game_data, GameData)
        assert_false(self.update_channel.recv_ready(), "Update channel has more messages")

    def test_game_data_is_initialized_with_lists(self):
        self.server._run_once()
        game_data = self.update_channel.recv()
        assert_is_instance(game_data.bullets, list)
        assert_is_instance(game_data.tanks, list)


if __name__ == "__main__":
    import nose
    nose.main()

