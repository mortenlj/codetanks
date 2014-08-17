#!/usr/bin/env python
# -*- coding: utf-8

from random import randint

from euclid import Point2, Vector2
from hamcrest import assert_that, equal_to, instance_of
from mock import create_autospec, patch
from nose.tools import assert_is_instance, assert_equal, assert_true

from ibidem.codetanks.domain.constants import TANK_RADIUS
from ibidem.codetanks.domain.ttypes import Arena, Id, Tank, BotStatus, Bullet
from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.commands import Move
from ibidem.codetanks.server.vehicle import Armour, Missile
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
    def _bounds_test(self, vehicle_class, entity, parent, position, is_valid):
        if parent:
            vehicle = vehicle_class(entity, self.world, parent)
        else:
            vehicle = vehicle_class(entity, self.world)
        vehicle.position = position
        assert_that(self.world.is_valid_position(vehicle), equal_to(is_valid))

    def test_bounds(self):
        for cls, entity, parent in (Armour, create_autospec(Tank), None), (Missile, create_autospec(Bullet), create_autospec(Armour)):
            for x in (cls.radius, self.width/2, self.width-cls.radius):
                for y in (cls.radius, self.height/2, self.height-cls.radius):
                    yield self._bounds_test, cls, entity, parent, Point2(x, y), True
                for y in (-cls.radius, -1, 0, 1, self.height-1, self.height, self.height+1, self.height+cls.radius):
                    yield self._bounds_test, cls, entity, parent, Point2(x, y), False
            for x in (-cls.radius, -1, 0, 1, self.width-1, self.width, self.width+1, self.width+cls.radius):
                for y in (-cls.radius, -1, 0, 1, self.height-1, self.height, self.height+1, self.height+cls.radius):
                    yield self._bounds_test, cls, entity, parent, Point2(x, y), False
                for y in (cls.radius, self.height/2, self.height-cls.radius):
                    yield self._bounds_test, cls, entity, parent, Point2(x, y), False

    def test_simple_tank_collision(self):
        self.world.add_tank(Bot(self.bot_id, 0, None, None))
        self.world.add_tank(Bot(self.bot_id, 1, None, None))
        tank0 = self.world._tanks[0]
        tank0.position = Point2(50, 50)
        tank1 = self.world._tanks[1]
        tank1.position = Point2(50, 50)
        assert_that(self.world.is_valid_position(tank0), equal_to(False))


class TestTankCreation(Shared):
    def test_tank_is_placed_inside_arena(self):
        return_values = []
        return_values.extend([None]*4)
        for x in -TANK_RADIUS, -1, 0, 1, self.width-1, self.width, self.width+1, self.width+TANK_RADIUS:
            for y in -TANK_RADIUS, -1, 0, 1, self.height-1, self.height, self.height+1, self.height+TANK_RADIUS:
                return_values.append(x)
                return_values.append(y)
        return_values.append(self.width/2)
        return_values.append(self.height/2)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            self.world.add_tank(Bot(self.bot_id, 0, None, None))
            vehicle = self.world._tanks[0]
            tank = vehicle.entity
            assert_is_instance(tank, Tank)
            assert_true(self.world.is_valid_position(vehicle), "Position is invalid")
            assert_that(tank.position.x, equal_to(self.width/2))
            assert_that(tank.position.y, equal_to(self.height/2))

    def test_tank_has_sensible_values(self):
        self.world.add_tank(Bot(self.bot_id, 0, None, None))
        tank = self.world.tanks[0]
        assert_equal(tank.health, 100)
        assert_equal(tank.status, BotStatus.IDLE)

    def test_tank_has_valid_direction(self):
        return_values = [0, 0, 1, 0, 0, -1]
        return_values.extend([None]*10)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            self.world.add_tank(Bot(self.bot_id, 0, None, None))
            vehicle = self.world._tanks[0]
            tank = vehicle.entity
            assert_that(tank.direction.x, equal_to(0))
            assert_that(tank.direction.y, equal_to(1))
            assert_that(tank.turret.x, equal_to(0))
            assert_that(tank.turret.y, equal_to(-1))

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
        self.armour = create_autospec(Armour)
        self.world._tanks[self.tank_id] = self.armour

    def test_update_calls_armour_update(self):
        ticks = 10
        self.world.update(ticks)
        self.armour.update.assert_called_with(ticks)

    def _command_test(self, name, *params):
        self.world.command(self.tank_id, name, *params)
        func = getattr(self.armour, name)
        func.assert_called_with(*params)

    def test_commands_forwarded_to_vehicle(self):
        yield self._command_test, "move", 10
        yield self._command_test, "rotate", 10
        yield self._command_test, "aim", 10
        yield self._command_test, "fire"


class BulletShared(Shared):
    def setup(self):
        super(BulletShared, self).setup()
        self.parent = create_autospec(Armour)
        self.parent.position = Point2(230, 50)
        self.parent.turret = Vector2(-1, 0)


class TestBulletCreation(BulletShared):
    def test_bullet_is_placed_at_location(self):
        self.world.add_bullet(self.parent)
        bullet = self.world._bullets[0]
        assert_that(bullet.position, equal_to(self.parent.position))
        assert_that(bullet.direction, equal_to(self.parent.turret))
        assert_that(bullet._command, instance_of(Move))


class TestBulletMovement(BulletShared):
    position = Point2(250, 250)
    direction = Vector2(1, 0)

    def setup(self):
        super(TestBulletMovement, self).setup()
        self.world.add_bullet(self.parent)
        self.bullet = create_autospec(Missile)
        self.world._bullets[0] = self.bullet

    def test_update_calls_bullet_update(self):
        ticks = 10
        self.world.update(ticks)
        self.bullet.update.assert_called_with(ticks)


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
