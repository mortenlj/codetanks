#!/usr/bin/env python
# -*- coding: utf-8
from random import uniform
import math

from hamcrest import assert_that, equal_to, less_than, greater_than
from euclid import Point2, Vector2

from ibidem.codetanks.domain.constants import ROTATION_TOLERANCE
from ibidem.codetanks.domain.ttypes import Tank, Id, Point, BotStatus
from ibidem.codetanks.server.vehicle import Vehicle


def to_point(p):
    return Point(p.x, p.y)


class Shared(object):
    bot_id = Id("bot", 1)
    initial_x = 3
    initial_y = 5
    initial_direction = Point2(1, 0)
    initial_turret = Point2(-1, 0)

    def setup(self):
        self.tank = Tank(0,
                         self.bot_id,
                         Point(self.initial_x, self.initial_y),
                         to_point(self.initial_direction),
                         to_point(self.initial_turret))
        self.vehicle = Vehicle(self.tank)


class TestVehicle(Shared):
    def test_properties_reflect_entity(self):
        assert_that(self.vehicle.position.x, equal_to(self.tank.position.x))
        assert_that(self.vehicle.position.y, equal_to(self.tank.position.y))
        assert_that(self.vehicle.direction.x, equal_to(self.tank.direction.x))
        assert_that(self.vehicle.direction.y, equal_to(self.tank.direction.y))

    def test_setting_position_is_applied_to_entity(self):
        new_position = Point2(13, 21)
        self.vehicle.position = new_position
        assert_that(self.tank.position.x, equal_to(new_position.x))
        assert_that(self.tank.position.y, equal_to(new_position.y))


class TestMove(Shared):
    def test_move_forwards(self):
        distance = 10
        target_x = self.initial_x + distance
        self.vehicle.move(distance)
        assert_that(self.vehicle.status, equal_to(BotStatus.MOVING))
        assert_that(self.vehicle.position.x, equal_to(self.initial_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))
        while self.vehicle.position.x < target_x:
            assert_that(self.vehicle.position.x, less_than(target_x))
            self.vehicle.update(random_ticks())
            assert_that(self.vehicle.position.x, greater_than(self.initial_x))
        assert_that(self.vehicle.status, equal_to(BotStatus.IDLE))
        assert_that(self.vehicle.position.x, equal_to(target_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))

    def test_move_backwards_is_illegal(self):
        self.vehicle.move(-10)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle.status, equal_to(BotStatus.IDLE))
        assert_that(self.vehicle.position.x, equal_to(self.initial_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))


class RotateAndAim(Shared):
    def _test(self, desc, angle, target_vector):
        self._act(angle)
        self._assert_starting_state()
        while self._continue(target_vector):
            self._assert_pre_update(target_vector)
            self.vehicle.update(random_ticks())
            self._assert_post_update(angle, target_vector)
        self._assert_ending_state(target_vector)


class TestRotate(RotateAndAim):
    def _assert_starting_state(self):
        assert_that(self.vehicle.status, equal_to(BotStatus.ROTATING))
        assert_that_vector_matches(self.vehicle.direction, self.initial_direction, equal_to(0.0))

    def _assert_ending_state(self, target_vector):
        assert_that(self.vehicle.status, equal_to(BotStatus.IDLE))
        assert_that_vector_matches(self.vehicle.direction, target_vector, equal_to(0.0))

    def _continue(self, target_vector):
        return self.vehicle.direction.angle(target_vector) != 0.0

    def _assert_pre_update(self, target_vector):
        assert_that_vector_matches(self.vehicle.direction, target_vector, greater_than(0.0))

    def _assert_post_update(self, angle, target_vector):
        assert_that_vector_matches(self.vehicle.direction, target_vector, less_than(abs(angle)))

    def test_rotation(self):
        yield ("_test", "anti-clockwise", math.pi / 2, Vector2(0, 1))
        yield ("_test", "clockwise", -math.pi / 2, Vector2(0, -1))

    def test_rotation_less_than_tolerance_is_illegal(self):
        self.vehicle.rotate(ROTATION_TOLERANCE-.001)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle.direction, equal_to(self.initial_direction))

    def _act(self, angle):
        self.vehicle.rotate(angle)


class TestAim(RotateAndAim):
    def _assert_starting_state(self):
        assert_that(self.vehicle.status, equal_to(BotStatus.AIMING))
        assert_that_vector_matches(self.vehicle.turret, self.initial_turret, equal_to(0.0))

    def _assert_ending_state(self, target_vector):
        assert_that(self.vehicle.status, equal_to(BotStatus.IDLE))
        assert_that_vector_matches(self.vehicle.turret, target_vector, equal_to(0.0))

    def _continue(self, target_vector):
        return self.vehicle.turret.angle(target_vector) != 0.0

    def _assert_pre_update(self, target_vector):
        assert_that_vector_matches(self.vehicle.turret, target_vector, greater_than(0.0))

    def _assert_post_update(self, angle, target_vector):
        assert_that_vector_matches(self.vehicle.turret, target_vector, less_than(abs(angle)))

    def test_aim(self):
        yield ("_test", "anti-clockwise", math.pi / 2, Vector2(0, -1))
        yield ("_test", "clockwise", -math.pi / 2, Vector2(0, 1))

    def test_aim_less_than_tolerance_is_illegal(self):
        self.vehicle.aim(ROTATION_TOLERANCE-.001)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle.turret, equal_to(self.initial_turret))

    def _act(self, angle):
        self.vehicle.aim(angle)


def assert_that_vector_matches(actual, expected, matcher):
    assert_that(actual.angle(expected), matcher)


def random_ticks():
    return int(uniform(5.0, 15.0))


if __name__ == "__main__":
    import nose
    nose.main()
