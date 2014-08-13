#!/usr/bin/env python
# -*- coding: utf-8
from itertools import chain
from random import uniform

from mock import create_autospec
from hamcrest import assert_that, equal_to, less_than, greater_than, instance_of
from euclid import Point2, Vector2

from ibidem.codetanks.domain.constants import ROTATION_TOLERANCE, TANK_RADIUS, BULLET_RADIUS
from ibidem.codetanks.domain.ttypes import Tank, Id, Point, BotStatus, Bullet, Arena
from ibidem.codetanks.server.commands import Idle
from ibidem.codetanks.server.vehicle import Armour, Missile
from ibidem.codetanks.server.world import World


def to_point(p):
    return Point(p.x, p.y)


class Shared(object):
    bot_id = Id("bot", 1)
    initial_x = 30
    initial_y = 50
    initial_direction = Point2(1, 0)
    initial_turret = Point2(-1, 0)

    def setup_world(self):
        self.world = create_autospec(World)
        self.world.arena = Arena(500, 500)
        self.world.is_valid_position.return_value = True

    def setup(self):
        self.setup_world()
        self.tank = self._create_tank()
        self.vehicle = Armour(self.tank, self.world)

    def _create_tank(self, tank_id=0, position=None):
        if position is None:
            position = Point(self.initial_x, self.initial_y)
        return Tank(tank_id,
                    self.bot_id,
                    position,
                    to_point(self.initial_direction),
                    to_point(self.initial_turret))

    def _create_bullet(self, bullet_id=0, position=None):
        if position is None:
            position = Point(self.initial_x, self.initial_y)
        return Bullet(bullet_id, position, to_point(self.initial_direction))


class TestVehicle(Shared):
    def test_properties_reflect_entity(self):
        assert_that(self.vehicle.position.x, equal_to(self.tank.position.x))
        assert_that(self.vehicle.position.y, equal_to(self.tank.position.y))
        assert_that(self.vehicle.direction.x, equal_to(self.tank.direction.x))
        assert_that(self.vehicle.direction.y, equal_to(self.tank.direction.y))
        assert_that(self.vehicle.turret.x, equal_to(self.tank.turret.x))
        assert_that(self.vehicle.turret.y, equal_to(self.tank.turret.y))
        assert_that(self.vehicle.status, equal_to(self.tank.status))

    def test_setting_position_is_applied_to_entity(self):
        new_position = Point2(20, 40)
        self.vehicle.position = new_position
        assert_that(self.tank.position.x, equal_to(new_position.x))
        assert_that(self.tank.position.y, equal_to(new_position.y))

    def test_setting_direction_is_applied_to_entity(self):
        new_direction = Point2(1, -1)
        self.vehicle.direction = new_direction
        assert_that(self.tank.direction.x, equal_to(new_direction.x))
        assert_that(self.tank.direction.y, equal_to(new_direction.y))

    def test_setting_turret_is_applied_to_entity(self):
        new_turret = Point2(1, -1)
        self.vehicle.turret = new_turret
        assert_that(self.tank.turret.x, equal_to(new_turret.x))
        assert_that(self.tank.turret.y, equal_to(new_turret.y))

    def test_setting_status_is_applied_to_entity(self):
        status = BotStatus.MOVING
        self.vehicle.status = status
        assert_that(self.tank.status, equal_to(status))


class TestMove(Shared):
    def test_move_forwards(self):
        distance = 10
        target_x = self.initial_x + distance
        self.vehicle.move(distance)
        assert_that(self.vehicle.status, equal_to(BotStatus.MOVING))
        assert_that(self.vehicle.position.x, equal_to(self.initial_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))
        while self.vehicle.position.x < target_x:
            assert_that(self.vehicle.status, equal_to(BotStatus.MOVING))
            assert_that(self.vehicle.position.x, less_than(target_x))
            self.vehicle.update(random_ticks())
            assert_that(self.vehicle.position.x, greater_than(self.initial_x))
        assert_that(self.vehicle._command, instance_of(Idle))
        assert_that(self.vehicle.position.x, equal_to(target_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))

    def test_move_backwards_is_illegal(self):
        self.vehicle.move(-10)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle._command, instance_of(Idle))
        assert_that(self.vehicle.position.x, equal_to(self.initial_x))
        assert_that(self.vehicle.position.y, equal_to(self.initial_y))

    def test_world_is_checked_for_valid_position(self):
        self.vehicle.move(1)
        self.vehicle.update(10)
        self.world.is_valid_position.assert_called_once_with(self.vehicle)

    def test_world_is_checked_for_valid_position_for_missile(self):
        missile = Missile(self._create_bullet(0), self.world, self.vehicle)
        missile.update(random_ticks())
        self.world.is_valid_position.assert_called_once_with(missile)

    def test_vehicle_is_not_moved_if_new_position_invalid(self):
        self.world.is_valid_position.return_value = False
        missile = Missile(self._create_bullet(0), self.world, self.vehicle)
        missile.update(random_ticks())
        assert_that(missile.position.x, equal_to(self.initial_x))
        assert_that(missile.position.y, equal_to(self.initial_y))
        self.vehicle.move(100)
        self.vehicle.update(random_ticks())
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
        assert_that(self.vehicle._command, instance_of(Idle))
        assert_that_vector_matches(self.vehicle.direction, target_vector, equal_to(0.0))

    def _continue(self, target_vector):
        return self.vehicle.direction.angle(target_vector) != 0.0

    def _assert_pre_update(self, target_vector):
        assert_that(self.vehicle.status, equal_to(BotStatus.ROTATING))
        assert_that_vector_matches(self.vehicle.direction, target_vector, greater_than(0.0))

    def _assert_post_update(self, angle, target_vector):
        assert_that_vector_matches(self.vehicle.direction, target_vector, less_than(abs(angle)))

    def test_rotation(self):
        yield ("_test", "anti-clockwise", 90, Vector2(0, 1))
        yield ("_test", "clockwise", -90, Vector2(0, -1))

    def test_rotation_less_than_tolerance_is_illegal(self):
        self.vehicle.rotate(1)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle.direction, equal_to(self.initial_direction))
        assert_that(self.vehicle._command, instance_of(Idle))

    def _act(self, angle):
        self.vehicle.rotate(angle)


class TestAim(RotateAndAim):
    def _assert_starting_state(self):
        assert_that(self.vehicle.status, equal_to(BotStatus.AIMING))
        assert_that_vector_matches(self.vehicle.turret, self.initial_turret, equal_to(0.0))

    def _assert_ending_state(self, target_vector):
        assert_that(self.vehicle._command, instance_of(Idle))
        assert_that_vector_matches(self.vehicle.turret, target_vector, equal_to(0.0))

    def _continue(self, target_vector):
        return self.vehicle.turret.angle(target_vector) != 0.0

    def _assert_pre_update(self, target_vector):
        assert_that(self.vehicle.status, equal_to(BotStatus.AIMING))
        assert_that_vector_matches(self.vehicle.turret, target_vector, greater_than(0.0))

    def _assert_post_update(self, angle, target_vector):
        assert_that_vector_matches(self.vehicle.turret, target_vector, less_than(abs(angle)))

    def test_aim(self):
        yield ("_test", "anti-clockwise", 90, Vector2(0, -1))
        yield ("_test", "clockwise", -90, Vector2(0, 1))

    def test_aim_less_than_tolerance_is_illegal(self):
        self.vehicle.aim(ROTATION_TOLERANCE-.001)
        self.vehicle.update(random_ticks())
        assert_that(self.vehicle.turret, equal_to(self.initial_turret))
        assert_that(self.vehicle._command, instance_of(Idle))

    def _act(self, angle):
        self.vehicle.aim(angle)


class TestFire(Shared):
    def test_fire(self):
        self.vehicle.fire()
        self.vehicle.update(random_ticks())
        self.world.add_bullet.assert_called_with(self.vehicle)


class TestCollide(Shared):
    def _collide_test(self, other, result):
        assert_that(self.vehicle.collide(other), equal_to(result))

    def _point_generator(self, modifier):
        yield Point(self.initial_x - modifier, self.initial_y)
        yield Point(self.initial_x + modifier, self.initial_y)
        yield Point(self.initial_x, self.initial_y - modifier)
        yield Point(self.initial_x, self.initial_y + modifier)

    def test_armour_overlap_with_armour_is_detected(self):
        self.setup_world()
        modifiers = (2*TANK_RADIUS, (2*TANK_RADIUS-1), TANK_RADIUS, 1)
        for modifier in modifiers:
            for pos in self._point_generator(modifier):
                yield ("_collide_test", Armour(self._create_tank(1, pos), self.world), True)
        yield ("_collide_test", Armour(self._create_tank(1, Point(self.initial_x, self.initial_y)), self.world), True)

    def test_armour_overlap_with_missile_is_detected(self):
        self.setup_world()
        modifiers = (2*BULLET_RADIUS, (2*BULLET_RADIUS-1), BULLET_RADIUS, 1)
        for modifier in modifiers:
            for pos in self._point_generator(modifier):
                yield ("_collide_test", Missile(self._create_bullet(0, pos), self.world, None), True)
            yield ("_collide_test", Missile(self._create_bullet(0, Point(self.initial_x, self.initial_y)), self.world, None), True)

    def test_armour_non_overlap_is_accepted(self):
        self.setup_world()
        abs_modifiers = (2*TANK_RADIUS+1, 3*TANK_RADIUS)
        modifiers = list(chain(abs_modifiers, (-1*m for m in abs_modifiers)))
        for x in (self.initial_x + modifier for modifier in modifiers):
            for y in (self.initial_y + modifier for modifier in modifiers):
                yield ("_collide_test", Armour(self._create_tank(1, Point(x, y)), self.world), False)

    def test_missile_non_overlap_is_accepted(self):
        self.setup_world()
        abs_modifiers = (TANK_RADIUS+BULLET_RADIUS+1, TANK_RADIUS+2*BULLET_RADIUS)
        modifiers = list(chain(abs_modifiers, (-1*m for m in abs_modifiers)))
        for x in (self.initial_x + modifier for modifier in modifiers):
            for y in (self.initial_y + modifier for modifier in modifiers):
                yield ("_collide_test", Missile(self._create_bullet(0, Point(x, y)), self.world, None), False)

    def test_vehicle_does_not_collide_with_self(self):
        assert_that(self.vehicle.collide(self.vehicle), equal_to(False))
        missile = Missile(self._create_bullet(), self.world, self.vehicle)
        assert_that(missile.collide(missile), equal_to(False))

    def test_missile_does_not_collide_with_parent(self):
        missile = Missile(self._create_bullet(), self.world, self.vehicle)
        assert_that(missile.collide(self.vehicle), equal_to(False))


def assert_that_vector_matches(actual, expected, matcher):
    assert_that(actual.angle(expected), matcher)


def random_ticks():
    return int(uniform(5.0, 15.0))


if __name__ == "__main__":
    import nose
    nose.main()
