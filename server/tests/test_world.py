#!/usr/bin/env python
# -*- coding: utf-8

from random import randint

from euclid import Point2
from hamcrest import assert_that, equal_to
from mock import create_autospec, patch
from nose.tools import assert_is_instance, assert_equal, assert_true

from ibidem.codetanks.domain.constants import TANK_RADIUS
from ibidem.codetanks.domain.ttypes import Arena, Id, Tank, BotStatus
from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.vehicle import Vehicle
from ibidem.codetanks.server.world import World


class Shared(object):
    width = 500
    height = 500
    bot_id = Id("bot", 1)

    def setup(self):
        self.world = World(self.width, self.height)


class TestWorld(Shared):
    def test_game_data_is_initialized_with_lists(self):
        assert_is_instance(self.world.bullets, list)
        assert_is_instance(self.world.tanks, list)

    def test_arena_is_given_size(self):
        assert_is_instance(self.world.arena, Arena)
        assert_equal(self.world.arena.width, self.width)
        assert_equal(self.world.arena.height, self.height)

    def test_gamedata_is_reflected_in_attributes(self):
        assert_equal(self.world.bullets, self.world.gamedata.bullets)
        assert_equal(self.world.tanks, self.world.gamedata.tanks)


class TestValidPosition(Shared):
    def _bounds_test(self, position, is_valid):
        assert_that(self.world.is_valid_position(position), equal_to(is_valid))

    def test_bounds(self):
        for x in (TANK_RADIUS, self.width/2, self.width-TANK_RADIUS):
            for y in (TANK_RADIUS, self.height/2, self.height-TANK_RADIUS):
                yield ("_bounds_test", Point2(x, y), True)
            for y in (-TANK_RADIUS, -1, 0, 1, self.height-1, self.height, self.height+1, self.height+TANK_RADIUS):
                yield ("_bounds_test", Point2(x, y), False)
        for x in (-TANK_RADIUS, -1, 0, 1, self.width-1, self.width, self.width+1, self.width+TANK_RADIUS):
            for y in (-TANK_RADIUS, -1, 0, 1, self.height-1, self.height, self.height+1, self.height+TANK_RADIUS):
                yield ("_bounds_test", Point2(x, y), False)
            for y in (TANK_RADIUS, self.height/2, self.height-TANK_RADIUS):
                yield ("_bounds_test", Point2(x, y), False)


class TestTankCreation(Shared):
    def test_tank_is_placed_inside_arena(self):
        return_values = []
        for x in -TANK_RADIUS, -1, 0, 1, self.width-1, self.width, self.width+1, self.width+TANK_RADIUS:
            for y in -TANK_RADIUS, -1, 0, 1, self.height-1, self.height, self.height+1, self.height+TANK_RADIUS:
                return_values.append(x)
                return_values.append(y)
        return_values.append(self.width/2)
        return_values.append(self.height/2)
        return_values.extend([None]*4)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            self.world.add_tank(Bot(self.bot_id, 0, None, None))
            tank = self.world.tanks[0]
            assert_is_instance(tank, Tank)
            assert_true(self.world.is_valid_position(tank.position), "Position is invalid")
            assert_that(tank.position.x, equal_to(self.width/2))
            assert_that(tank.position.y, equal_to(self.height/2))

    def test_tank_has_sensible_values(self):
        self.world.add_tank(Bot(self.bot_id, 0, None, None))
        tank = self.world.tanks[0]
        assert_equal(tank.health, 100)
        assert_equal(tank.status, BotStatus.IDLE)

    def test_tank_status(self):
        self.world.add_tank(Bot(self.bot_id, 0, None, None))
        tank = self.world.tanks[0]
        for status in BotStatus._NAMES_TO_VALUES.values():
            tank.status = status
            assert_equal(self.world.tank_status(tank.id), status)


class TestTankMovement(Shared):
    tank_id = 0

    def setup(self):
        super(TestTankMovement, self).setup()
        self.world.add_tank(Bot(self.bot_id, 0, None, None))
        self.vehicle = create_autospec(Vehicle)
        self.world._tanks[self.tank_id] = self.vehicle

    def test_update_calls_vehicle_update(self):
        ticks = 10
        self.world.update(ticks)
        self.vehicle.update.assert_called_with(ticks)

    def test_move_actions_forwarded_to_vehicle(self):
        distance = 10
        self.world.move(self.tank_id, distance)
        self.vehicle.move.assert_called_with(distance)

    def test_rotate_actions_forwarded_to_vehicle(self):
        angle = 1.0
        self.world.rotate(self.tank_id, angle)
        self.vehicle.rotate.assert_called_with(angle)

    def test_aim_actions_forwarded_to_vehicle(self):
        angle = 1.0
        self.world.aim(self.tank_id, angle)
        self.vehicle.aim.assert_called_with(angle)


class _MyRandint(object):
    def __init__(self, return_values):
        self.return_values = list(return_values)

    def __call__(self, *args, **kwargs):
        if self.return_values:
            value = self.return_values.pop(0)
            return randint(*args, **kwargs) if value is None else value
        assert False, "Not enough return values"

if __name__ == "__main__":
    import nose
    nose.main()
