#!/usr/bin/env python
# -*- coding: utf-8

from nose.tools import assert_is_not_none, assert_equal, assert_false, assert_true

from ibidem.codetanks.server.game_server import GameServer


class TestGameServerBounds(object):
    def setup(self):
        self.server = GameServer()

    def test_server_has_bounds(self):
        assert_is_not_none(self.server.bounds)

    def test_server_bounds_are_valid(self):
        assert_equal(self.server.bounds.left, 0)
        assert_equal(self.server.bounds.width, 500)
        assert_equal(self.server.bounds.top, 0)
        assert_equal(self.server.bounds.height, 500)

    def test_server_returns_bounds_in_info(self):
        game_info = self.server.build_game_info()
        bounds = game_info["arena"]
        assert_equal(bounds["height"], self.server.bounds.height)
        assert_equal(bounds["width"], self.server.bounds.width)


class TestGameServerState(object):
    def setup(self):
        self.server = GameServer()

    def test_new_server_is_not_started(self):
        assert_false(self.server.started())

    def test_started_server_is_started(self):
        self.server.start()
        assert_true(self.server.started())

if __name__ == "__main__":
    import nose
    nose.main()

