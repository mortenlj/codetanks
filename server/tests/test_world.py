#!/usr/bin/env python
# -*- coding: utf-8

import logging
from random import randint

import math
import pytest
from euclid import Point2, Vector2, Ray2
from mock import create_autospec, patch

from ibidem.codetanks.domain.messages_pb2 import Arena, Id, Tank, BotStatus, Bullet, ScanResult, Death, Event, Point
from ibidem.codetanks.server.commands import Move
from ibidem.codetanks.server.constants import TANK_RADIUS
from ibidem.codetanks.server.vehicle import Armour, Missile
from ibidem.codetanks.server.world import World

LOG = logging.getLogger(__name__)
WIDTH = 500
HEIGTH = 500
BOT_ID = Id(name="bot", version=1)
TANK_ID = 0
RAY = Ray2(Point2(200., 200.), Vector2(1., 1.))


@pytest.fixture
def world():
    return World(WIDTH, HEIGTH, False)


class TestWorld:
    @pytest.fixture(params=(
            (Armour, Tank(), None),
            (Missile, Bullet(), create_autospec(Armour))
    ))
    def vehicle(self, request):
        return request.param

    def test_game_data_is_initialized_with_lists(self, world):
        assert isinstance(world.bullets, list)
        assert isinstance(world.tanks, list)

    def test_arena_is_given_size(self, world):
        assert isinstance(world.arena, Arena)
        assert world.arena.width == WIDTH
        assert world.arena.height == HEIGTH

    def test_gamedata_is_reflected_in_attributes(self, world):
        assert world.bullets == list(world.gamedata.bullets)
        assert world.tanks == list(world.gamedata.tanks)

    def _bounds_test(self, world, vehicle_class, entity, parent, position, is_outside_bounds):
        entity.position.CopyFrom(Point(x=position.x, y=position.y))
        entity.direction.CopyFrom(Point(x=1, y=1))
        if parent:
            vehicle = vehicle_class(entity, world, parent)
        else:
            vehicle = vehicle_class(entity, world)
        assert world.is_collision(vehicle) is is_outside_bounds

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
    def test_bounds(self, world, vehicle, x_func, x_inside, y_func, y_inside):
        cls, entity, parent = vehicle
        x = x_func(cls, WIDTH)
        y = y_func(cls, HEIGTH)
        inside = x_inside and y_inside
        position = Point2(x, y)
        self._bounds_test(world, cls, entity, parent, position, not inside)

    def test_simple_tank_collision(self, world):
        tank0 = world.add_tank(BOT_ID, 0)
        tank1 = world.add_tank(BOT_ID, 1)
        tank0.position = Point2(50, 50)
        tank1.position = Point2(50, 50)
        assert world.is_collision(tank0) == tank1

    def test_tank_is_placed_inside_arena(self, world):
        return_values = []
        return_values.extend([1] * 4)
        for x in -TANK_RADIUS, -1, 0, 1, WIDTH - 1, WIDTH, WIDTH + 1, WIDTH + TANK_RADIUS:
            for y in -TANK_RADIUS, -1, 0, 1, HEIGTH - 1, HEIGTH, HEIGTH + 1, HEIGTH + TANK_RADIUS:
                return_values.append(x)
                return_values.append(y)
        return_values.append(WIDTH / 2)
        return_values.append(HEIGTH / 2)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            vehicle = world.add_tank(BOT_ID, 0)
            tank = vehicle.entity
            assert isinstance(tank, Tank)
            assert not world.is_collision(vehicle)
            assert tank.position.x == WIDTH / 2
            assert tank.position.y == HEIGTH / 2

    def test_tank_has_sensible_values(self, world):
        tank = world.add_tank(BOT_ID, 0)
        assert tank.health == 100
        assert tank.status == BotStatus.IDLE

    def test_tank_has_valid_direction(self, world):
        return_values = [0, 0, 1, 0, 0, -1]
        return_values.extend([None] * 10)
        with patch("ibidem.codetanks.server.world.randint", side_effect=_MyRandint(return_values)):
            vehicle = world.add_tank(BOT_ID, 0)
            tank = vehicle.entity
            assert tank.direction.x == 0
            assert tank.direction.y == 1
            assert tank.turret.x == 0
            assert tank.turret.y == -1

    def test_added_tank_is_returned(self, world):
        returned_tank = world.add_tank(BOT_ID, 0)
        added_tank = world._tanks[0]
        assert returned_tank is added_tank


class TestTank:
    @pytest.fixture
    def armour(self):
        armour = create_autospec(Armour)
        armour.entity = Tank()
        armour.radius = TANK_RADIUS
        return armour

    @pytest.fixture
    def world(self, world, armour):
        world.add_tank(BOT_ID, TANK_ID)
        world._tanks[TANK_ID] = armour
        return world

    def test_update_calls_armour_update(self, world, armour):
        ticks = 10
        world.update(ticks)
        armour.update.assert_called_with(ticks)

    def test_events_gathered(self, world):
        event = Event(scan=ScanResult(tanks=[]))
        world.add_event(TANK_ID, event)
        event_map = world.get_events()
        assert TANK_ID in event_map.keys()
        assert event in event_map[TANK_ID]

    def test_events_to_none_are_gathered(self, world):
        event = Event(death=Death(victim=Tank(), perpetrator=Tank()))
        world.add_event(None, event)
        event_map = world.get_events()
        assert None in event_map.keys()
        assert event in event_map[None]

    class TestScanWorld:
        @pytest.fixture
        def scan_params(self, request):
            func = request.param
            return getattr(self, func)()

        @pytest.fixture(params=range(10, 91, 5))
        def angle(self, request):
            return request.param

        @pytest.mark.parametrize("scan_params", (
                "_scan_radius_close",
                "_scan_radius_close",
                "_scan_catches_tank_off_center",
                "_scan_ignores_tank_at_center",
        ), indirect=True)
        def test_scan(self, armour, world, scan_params):
            position, angle, theta, assert_func_name = scan_params
            self._test_scan(armour, world, position, theta, assert_func_name)

        def _test_scan(self, armour, world, position, theta, assert_func_name):
            armour.position = position
            event = world.scan(RAY, theta)
            assert isinstance(event, Event)
            assert_func = getattr(self, assert_func_name)
            assert_func(armour, event.scan)

        def _assert_found_tank(self, armour, scan_result):
            assert list(scan_result.tanks) == [armour.entity]

        def _assert_no_tanks_found(self, armour, scan_result):
            assert list(scan_result.tanks) == []

        def _scan_radius_close(self):
            close_position = RAY.p + Vector2(50., 50.)
            theta = (math.pi / 2.)
            return close_position, 90, theta, "_assert_found_tank"

        def _scan_radius_far(self):
            far_position = RAY.p + Vector2(250., 250.)
            theta = (math.pi / 2.)
            return far_position, 90, theta, "_assert_no_tanks_found"

        def _scan_catches_tank_off_center(self):
            base_vector = Vector2(1., 1.)
            angle = 10
            theta = math.pi / 180. * angle
            position_vector = base_vector.rotate(theta) * 100
            position = RAY.p + position_vector
            return position, angle, theta, "_assert_found_tank"

        def _scan_ignores_tank_at_center(self):
            return RAY.p, 90, math.pi / 2., "_assert_no_tanks_found"

        @pytest.mark.parametrize("offset, assert_func_name", (
                (3., "_assert_found_tank"),
                (1., "_assert_no_tanks_found"),
        ))
        def test_scan_angles(self, armour, world, angle, offset, assert_func_name):
            base_vector = Vector2(1., 1.)
            theta = (math.pi / 180.) * angle
            vector = base_vector.rotate(theta / offset) * 150
            position = RAY.p + vector
            self._test_scan(armour, world, position, theta, assert_func_name)

        @pytest.mark.parametrize("theta, factor", (
                (math.pi, 0.0),
                (math.pi / 2, 0.5),
                (math.pi / 3, (2. / 3.)),
                (0.0, 1.0),
        ))
        def test_radius_calculator(self, world, theta, factor):
            radius = world.arena.height * factor
            assert world._calculate_scan_radius(theta) == pytest.approx(radius, abs=2.)


class TestBullet:
    @pytest.fixture
    def parent(self):
        parent = create_autospec(Armour)
        parent.position = Point2(230, 50)
        parent.turret = Vector2(-1, 0)
        return parent

    @pytest.fixture
    def bullet(self):
        return create_autospec(Missile)

    @pytest.fixture
    def world(self, world, parent, bullet):
        world.add_bullet(parent)
        world._bullets[0] = bullet
        return world

    def test_bullet_is_placed_at_location(self, world, parent):
        world.add_bullet(parent)
        bullet = world._bullets[-1]
        assert bullet.position == parent.position
        assert bullet.direction == parent.turret
        assert isinstance(bullet._command, Move)

    def test_update_calls_bullet_update(self, world, bullet):
        ticks = 10
        world.update(ticks)
        bullet.update.assert_called_with(ticks)

    def test_correct_bullet_is_removed(self, world, parent):
        world.add_bullet(parent)
        world.add_bullet(parent)
        first, to_remove, last = world._bullets
        world.remove_bullet(to_remove)
        assert len(world._bullets) == 2
        assert world._bullets[0] == first
        assert world._bullets[-1] == last


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
