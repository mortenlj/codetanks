#!/usr/bin/env python
# -*- coding: utf-8
from random import uniform
import math

from hamcrest import assert_that, equal_to, less_than, greater_than
from euclid import Point2, Ray2, Vector2

from ibidem.codetanks.domain.constants import TANK_SPEED
from ibidem.codetanks.domain.ttypes import Tank, Id, Point
from ibidem.codetanks.server.vehicle import Vehicle


def to_point(p):
    return Point(p.x, p.y)


class Shared(object):
    bot_id = Id("bot", 1)
    initial_x = 3
    initial_y = 5
    initial_direction = Point2(1, 0)

    def setUp(self):
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

    def test_update_position(self):
        distance = 10
        self.vehicle._meta.target_ray = Ray2(self.vehicle._calculate_new_position(distance), self.vehicle.direction)
        self.vehicle._meta.speed = TANK_SPEED
        self.vehicle.update_position(distance)
        assert_that(self.tank.position.x, equal_to(self.initial_x + (TANK_SPEED * distance)))
        assert_that(self.tank.position.y, equal_to(self.initial_y))


class TestMove(Shared):
    def test_move_forwards(self):
        distance = 10
        target_x = self.initial_x + distance
        self.vehicle.move(distance)
        assert_that(self.vehicle._meta.speed, equal_to(TANK_SPEED))
        assert_that(self.vehicle.position.x, equal_to(self.initial_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))
        while self.vehicle.position.x < target_x:
            assert_that(self.vehicle._meta.speed, equal_to(TANK_SPEED))
            assert_that(self.vehicle.position.x, less_than(target_x))
            self.vehicle.update_position(random_ticks())
            assert_that(self.vehicle.position.x, greater_than(self.initial_x))
        assert_that(self.vehicle._meta.speed, equal_to(0.0))
        assert_that(self.vehicle.position.x, equal_to(target_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))

    def test_move_backwards_is_illegal(self):
        self.vehicle.move(-10)
        self.vehicle.update_position(random_ticks())
        assert_that(self.vehicle._meta.speed, equal_to(0.0))
        assert_that(self.vehicle.position.x, equal_to(self.initial_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))


class TestRotate(Shared):
    def test_rotate_anti_clockwise(self):
        angle = math.pi / 2
        target_vector = Vector2(0, 1)
        self.vehicle.rotate(angle)
        assert_that_vector_matches(self.vehicle._meta.target_direction, target_vector, equal_to(0.0))
        assert_that_vector_matches(self.vehicle.direction, self.initial_direction, equal_to(0.0))
        while self.vehicle.direction.angle(target_vector) != 0.0:
            assert_that_vector_matches(self.vehicle.direction, target_vector, greater_than(0.0))
            self.vehicle.update_direction(random_ticks())
            assert_that_vector_matches(self.vehicle.direction, target_vector, less_than(angle))
        assert_that_vector_matches(self.vehicle.direction, target_vector, equal_to(0.0))

    def test_rotate_clockwise(self):
        angle = -math.pi / 2
        target_vector = Vector2(0, -1)
        self.vehicle.rotate(angle)
        assert_that_vector_matches(self.vehicle._meta.target_direction, target_vector, equal_to(0.0))
        assert_that_vector_matches(self.vehicle.direction, self.initial_direction, equal_to(0.0))
        while self.vehicle.direction.angle(target_vector) != 0.0:
            assert_that_vector_matches(self.vehicle.direction, target_vector, greater_than(0.0))
            self.vehicle.update_direction(random_ticks())
            assert_that_vector_matches(self.vehicle.direction, target_vector, less_than(abs(angle)))
        assert_that_vector_matches(self.vehicle.direction, target_vector, equal_to(0.0))


def assert_that_vector_matches(actual, expected, matcher):
    assert_that(actual.angle(expected), matcher)


def random_ticks():
    return int(uniform(5.0, 15.0))


if __name__ == "__main__":
    import nose
    nose.main()
