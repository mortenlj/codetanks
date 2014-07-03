#!/usr/bin/env python
# -*- coding: utf-8

from nose.tools import assert_is_instance, assert_equal

from ibidem.codetanks.domain.ttypes import Arena
from ibidem.codetanks.server.world import World


class TestWorld(object):
    width = 500
    height = 500

    def test_world_is_initialized_with_lists(self):
        world = World(self.width, self.height)
        assert_is_instance(world.bullets, list)
        assert_is_instance(world.tanks, list)

    def test_arena_is_given_size(self):
        world = World(self.width, self.height)
        assert_is_instance(world.arena, Arena)
        assert_equal(world.arena.width, self.width)
        assert_equal(world.arena.height, self.height)


if __name__ == "__main__":
    import nose
    nose.main()
