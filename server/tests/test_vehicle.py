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

    def setup(self):
        self.tank = Tank(0, self.bot_id, Point(self.initial_x, self.initial_y), to_point(self.initial_direction), Point(0, 1))
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


class TestRotate(Shared):
    def _rotation_test(self, desc, angle, target_vector):
        self.vehicle.rotate(angle)
        assert_that(self.vehicle.status, equal_to(BotStatus.ROTATING))
        assert_that_vector_matches(self.vehicle._meta.target_direction, target_vector, equal_to(0.0))
        assert_that_vector_matches(self.vehicle.direction, self.initial_direction, equal_to(0.0))
        while self.vehicle.direction.angle(target_vector) != 0.0:
            assert_that_vector_matches(self.vehicle.direction, target_vector, greater_than(0.0))
            self.vehicle.update(random_ticks())
            assert_that_vector_matches(self.vehicle.direction, target_vector, less_than(abs(angle)))
        assert_that(self.vehicle.status, equal_to(BotStatus.IDLE))
        assert_that_vector_matches(self.vehicle.direction, target_vector, equal_to(0.0))

    def test_rotation(self):
        yield ("_rotation_test", "clockwise", math.pi / 2, Vector2(0, 1))
        yield ("_rotation_test", "anti-clockwise", -math.pi / 2, Vector2(0, -1))

    def test_rotation_less_than_tolerance_is_illegal(self):
        self.vehicle.rotate(ROTATION_TOLERANCE-.001)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle._meta.rotation, equal_to(0.0))
        assert_that(self.vehicle.direction, equal_to(self.initial_direction))


def assert_that_vector_matches(actual, expected, matcher):
    assert_that(actual.angle(expected), matcher)


def random_ticks():
    return int(uniform(5.0, 15.0))


if __name__ == "__main__":
    import nose
    nose.main()
