#!/usr/bin/env python
# -*- coding: utf-8

import logging
import math
from random import randint

import pytest
from euclid import Point2, Vector2, Ray2
from hamcrest import assert_that, is_, equal_to, instance_of, has_key, has_item, close_to
from mock import create_autospec, patch

from ibidem.codetanks.domain.constants import TANK_RADIUS
from ibidem.codetanks.domain.ttypes import Arena, Id, Tank, BotStatus, Bullet, ScanResult, Death, Event
from ibidem.codetanks.server.commands import Move
from ibidem.codetanks.server.vehicle import Armour, Missile
from ibidem.codetanks.server.world import World

LOG = logging.getLogger(__name__)
DELTA = 0.000001


class Shared(object):
    width = 500
    height = 500
    bot_id = Id("bot", 1)

    def setup(self):
        self.world = World(self.width, self.height, False)


class TestWorld(Shared):
    def test_game_data_is_initialized_with_lists(self):
        assert_that(self.world.bullets, instance_of(list))
        assert_that(self.world.tanks, instance_of(list))

    def test_arena_is_given_size(self):
        assert_that(self.world.arena, instance_of(Arena))
        assert_that(self.world.arena.width, equal_to(self.width))
        assert_that(self.world.arena.height, equal_to(self.height))

    def test_gamedata_is_reflected_in_attributes(self):
        assert_that(self.world.bullets, equal_to(self.world.gamedata.bullets))
        assert_that(self.world.tanks, equal_to(self.world.gamedata.tanks))


class TestValidPosition(Shared):
    @pytest.fixture(params=(
            (Armour, create_autospec(Tank), None),
            (Missile, create_autospec(Bullet), create_autospec(Armour))
    ))
    def vehicle(self, request):
        return request.param

    def _bounds_test(self, vehicle_class, entity, parent, position, is_outside_bounds):
        if parent:
            vehicle = vehicle_class(entity, self.world, parent)
        else:
            vehicle = vehicle_class(entity, self.world)
        vehicle.position = position
        assert_that(self.world.is_collision(vehicle), equal_to(is_outside_bounds))

    @pytest.mark.parametrize("x_func, x_inside", (
        pytest.param(lambda c, w: c.radius, True, id="x_left_inside"),
        pytest.param(lambda c, w: w / 2, True, id="x_middle_inside"),
        pytest.param(lambda c, w: w - c.radius, True, id="x_right_inside"),
        pytest.param(lambda c, w: -c.radius, False, id="x_right_outside"),
        pytest.param(lambda c, w: -1, False, id="x_right_just_outside"),
        pytest.param(lambda c, w: 0, False, id="x_right_on_the_line"),
        pytest.param(lambda c, w: 1, False, id="x_right_just_inside"),
        pytest.param(lambda c, w: w - 1, False, id="x_left_just_inside"),
        pytest.param(lambda c, w: w, False, id="x_left_on_the_line"),
        pytest.param(lambda c, w: w + 1, False, id="x_left_just_outside"),
        pytest.param(lambda c, w: w + c.radius, False, id="x_left_outside"),
    ))
    @pytest.mark.parametrize("y_func, y_inside", (
        pytest.param(lambda c, h: c.radius, True, id="y_bottom_inside"),
        pytest.param(lambda c, h: h / 2, True, id="y_middle_inside"),
        pytest.param(lambda c, h: h - c.radius, True, id="y_top_inside"),
        pytest.param(lambda c, h: -c.radius, False, id="y_bottom_outside"),
        pytest.param(lambda c, h: -1, False, id="y_bottom_just_outside"),
        pytest.param(lambda c, h: 0, False, id="y_bottom_on_the_line"),
        pytest.param(lambda c, h: 1, False, id="y_bottom_just_inside"),
        pytest.param(lambda c, h: h - 1, False, id="y_top_just_inside"),
        pytest.param(lambda c, h: h, False, id="y_top_on_the_line"),
        pytest.param(lambda c, h: h + 1, False, id="y_top_just_outside"),
        pytest.param(lambda c, h: h + c.radius, False, id="y_top_outside"),
    ))
    def test_bounds(self, vehicle, x_func, x_inside, y_func, y_inside):
        cls, entity, parent = vehicle
        x = x_func(cls, self.width)
        y = y_func(cls, self.height)
        inside = x_inside and y_inside
        position = Point2(x, y)
        self._bounds_test(cls, entity, parent, position, not inside)

    def test_simple_tank_collision(self):
        tank0 = self.world.add_tank(self.bot_id, 0)
        tank1 = self.world.add_tank(self.bot_id, 1)
        tank0.position = Point2(50, 50)
        tank1.position = Point2(50, 50)
        assert_that(self.world.is_collision(tank0), equal_to(tank1))


class TestTankCreation(Shared):
    def test_tank_is_placed_inside_arena(self):
        return_values = []
        return_values.extend([1] * 4)
        for x in -TANK_RADIUS, -1, 0, 1, self.width - 1, self.width, self.width + 1, self.width + TANK_RADIUS:
            for y in -TANK_RADIUS, -1, 0, 1, self.height - 1, self.height, self.height + 1, self.height + TANK_RADIUS:
                return_values.append(x)
                return_values.append(y)
        return_values.append(self.width / 2)
        return_values.append(self.height / 2)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            vehicle = self.world.add_tank(self.bot_id, 0)
            tank = vehicle.entity
            assert_that(tank, instance_of(Tank))
            assert_that(self.world.is_collision(vehicle), equal_to(False), "%r has invalid position" % vehicle)
            assert_that(tank.position.x, equal_to(self.width / 2))
            assert_that(tank.position.y, equal_to(self.height / 2))

    def test_tank_has_sensible_values(self):
        tank = self.world.add_tank(self.bot_id, 0)
        assert_that(tank.health, equal_to(100))
        assert_that(tank.status, equal_to(BotStatus.IDLE))

    def test_tank_has_valid_direction(self):
        return_values = [0, 0, 1, 0, 0, -1]
        return_values.extend([None] * 10)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            vehicle = self.world.add_tank(self.bot_id, 0)
            tank = vehicle.entity
            assert_that(tank.direction.x, equal_to(0))
            assert_that(tank.direction.y, equal_to(1))
            assert_that(tank.turret.x, equal_to(0))
            assert_that(tank.turret.y, equal_to(-1))

    def test_added_tank_is_returned(self):
        returned_tank = self.world.add_tank(self.bot_id, 0)
        added_tank = self.world._tanks[0]
        assert_that(returned_tank, is_(added_tank))


class TankShared(Shared):
    tank_id = 0

    def setup(self):
        super(TankShared, self).setup()
        self.world.add_tank(self.bot_id, 0)
        self.armour = create_autospec(Armour)
        self.world._tanks[self.tank_id] = self.armour


class TestTankMovement(TankShared):
    def test_update_calls_armour_update(self):
        ticks = 10
        self.world.update(ticks)
        self.armour.update.assert_called_with(ticks)


class TestTankEvents(TankShared):
    def test_events_gathered(self):
        event = Event(scan=ScanResult([]))
        self.world.add_event(self.tank_id, event)
        event_map = self.world.get_events()
        assert_that(event_map, has_key(self.tank_id))
        assert_that(event_map[self.tank_id], has_item(event))

    def test_events_to_none_are_gathered(self):
        event = Event(death=Death(create_autospec(Tank), create_autospec(Tank)))
        self.world.add_event(None, event)
        event_map = self.world.get_events()
        assert_that(event_map, has_key(None))
        assert_that(event_map[None], has_item(event))


class TestScanWorld(TankShared):
    ray = Ray2(Point2(200., 200.), Vector2(1., 1.))

    def setup(self):
        super(TestScanWorld, self).setup()
        self.armour.entity = create_autospec(Tank)
        self.armour.radius = TANK_RADIUS

    @pytest.fixture
    def scan_params(self, request):
        func = request.param
        return getattr(self, func)()

    @pytest.mark.parametrize("scan_params", (
            "_scan_radius_close",
            "_scan_radius_close",
            "_scan_catches_tank_off_center",
            "_scan_ignores_tank_at_center",
    ), indirect=True)
    def test_scan(self, scan_params):
        position, angle, theta, assert_func_name = scan_params
        self._test_scan(position, theta, assert_func_name)

    def _test_scan(self, position, theta, assert_func_name):
        self.armour.position = position
        event = self.world.scan(self.ray, theta)
        assert_that(event, instance_of(Event))
        assert_func = getattr(self, assert_func_name)
        assert_func(event.scan)

    def _assert_found_tank(self, scan_result):
        assert scan_result.tanks == [self.armour.entity]

    def _assert_no_tanks_found(self, scan_result):
        assert scan_result.tanks == []

    def _scan_radius_close(self):
        close_position = self.ray.p + Vector2(50., 50.)
        theta = (math.pi / 2.)
        return close_position, 90, theta, "_assert_found_tank"

    def _scan_radius_far(self):
        far_position = self.ray.p + Vector2(250., 250.)
        theta = (math.pi / 2.)
        return far_position, 90, theta, "_assert_no_tanks_found"

    def _scan_catches_tank_off_center(self):
        base_vector = Vector2(1., 1.)
        angle = 10
        theta = math.pi / 180. * angle
        position_vector = base_vector.rotate(theta) * 100
        position = self.ray.p + position_vector
        return position, angle, theta, "_assert_found_tank"

    def _scan_ignores_tank_at_center(self):
        return self.ray.p, 90, math.pi / 2., "_assert_no_tanks_found"

    @pytest.fixture(params=range(10, 91, 5))
    def angle(self, request):
        return request.param

    @pytest.mark.parametrize("offset, assert_func_name", (
            (3., "_assert_found_tank"),
            (1., "_assert_no_tanks_found"),
    ))
    def test_scan_angles(self, angle, offset, assert_func_name):
        base_vector = Vector2(1., 1.)
        theta = (math.pi / 180.) * angle
        vector = base_vector.rotate(theta / offset) * 150
        position = self.ray.p + vector
        self._test_scan(position, theta, assert_func_name)

    @pytest.mark.parametrize("theta, factor", (
            (math.pi, 0.0),
            (math.pi / 2, 0.5),
            (math.pi / 3, (2. / 3.)),
            (0.0, 1.0),
    ))
    def test_radius_calculator(self, theta, factor):
        radius = self.world.arena.height * factor
        assert_that(self.world._calculate_scan_radius(theta), close_to(radius, 2.))


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

    def test_correct_bullet_is_removed(self):
        self.world.add_bullet(self.parent)
        self.world.add_bullet(self.parent)
        first, to_remove, last = self.world._bullets
        self.world.remove_bullet(to_remove)
        assert_that(len(self.world._bullets), equal_to(2))
        assert_that(self.world._bullets[0], equal_to(first))
        assert_that(self.world._bullets[-1], equal_to(last))


class _MyRandint(object):
    def __init__(self, return_values):
        LOG.debug("Creating MyRandint with values: %r", return_values)
        self.return_values = list(return_values)

    def __call__(self, *args, **kwargs):
        LOG.debug("Returning 'random' value from list of %d elements: %r", len(self.return_values), self.return_values)
        if self.return_values:
            value = self.return_values.pop(0)
            return randint(*args, **kwargs) if value is None else value
        assert False, "Not enough return values"
