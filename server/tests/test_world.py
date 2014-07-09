#!/usr/bin/env python
# -*- coding: utf-8
from random import uniform

from nose.tools import assert_is_instance, assert_equal, assert_not_equal, assert_greater, assert_less

from ibidem.codetanks.domain.constants import TANK_SPEED
from ibidem.codetanks.domain.ttypes import Arena, Id, Tank, BotStatus, Point
from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.world import World


class Shared(object):
    width = 500
    height = 500
    bot_id = Id("bot", 1)


class TestWorld(Shared):
    def test_game_data_is_initialized_with_lists(self):
        world = World(self.width, self.height)
        assert_is_instance(world.bullets, list)
        assert_is_instance(world.tanks, list)

    def test_arena_is_given_size(self):
        world = World(self.width, self.height)
        assert_is_instance(world.arena, Arena)
        assert_equal(world.arena.width, self.width)
        assert_equal(world.arena.height, self.height)

    def test_gamedata_is_reflected_in_attributes(self):
        world = World(self.width, self.height)
        assert_equal(world.bullets, world.gamedata.bullets)
        assert_equal(world.tanks, world.gamedata.tanks)


class TestTankCreation(Shared):
    def test_tank_is_placed_inside_arena(self):
        world = World(self.width, self.height)
        world.add_tank(Bot(self.bot_id, 0, None, None))
        tank = world.tanks[0]
        assert_is_instance(tank, Tank)
        assert_greater(tank.position.x, 0)
        assert_greater(tank.position.y, 0)
        assert_less(tank.position.x, self.width)
        assert_less(tank.position.y, self.height)

    def test_second_tank_does_not_collide(self):
        world = World(self.width, self.height)
        world.add_tank(Bot(self.bot_id, 0, None, None))
        world.add_tank(Bot(self.bot_id, 1, None, None))
        tank1 = world.tanks[0]
        tank2 = world.tanks[1]
        assert_not_equal(tank1.position.x, tank2.position.x)
        assert_not_equal(tank1.position.y, tank2.position.y)

    def test_tank_has_sensible_values(self):
        world = World(self.width, self.height)
        world.add_tank(Bot(self.bot_id, 0, None, None))
        tank = world.tanks[0]
        assert_equal(tank.health, 100)
        assert_equal(tank.status, BotStatus.ALIVE)


class TestTankMovement(Shared):
    def setup(self):
        self.world = World(self.height, self.width)
        self.world.add_tank(Bot(self.bot_id, 0, None, None))
        self.tank = self.world.tanks[0]
        self.tank.position = Point(50, 50)
        self.tank.direction = Point(1.0, 0.0)
        self.tank.aim = Point(0.0, -1.0)

    def test_move_actions_moves_tank_and_then_stops(self):
        self.world.move(self.tank.id, 10)
        assert_equal(self.world._tanks[0].meta.speed, TANK_SPEED)
        assert_equal(self.tank.position.x, 50)
        assert_equal(self.tank.position.y, 50)
        while self.tank.position.x < 60:
            assert_equal(self.world._tanks[0].meta.speed, TANK_SPEED)
            assert_less(self.tank.position.x, 60)
            self.world.update(uniform(5.0, 15.0))
            assert_greater(self.tank.position.x, 50)
        assert_equal(self.world._tanks[0].meta.speed, 0.0)
        assert_equal(self.tank.position.x, 60)
        assert_equal(self.tank.position.y, 50)


if __name__ == "__main__":
    import nose
    nose.main()
