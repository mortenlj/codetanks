#!/usr/bin/env python
# -*- coding: utf-8
from itertools import chain
from random import uniform

from mock import create_autospec
from hamcrest import assert_that, equal_to, less_than, greater_than, instance_of, close_to, is_not, empty
from euclid import Point2, Vector2

from ibidem.codetanks.domain.constants import TANK_RADIUS, BULLET_RADIUS, MAX_HEALTH, BULLET_DAMAGE
from ibidem.codetanks.domain.ttypes import Tank, Id, Point, BotStatus, Bullet, Arena, ScanResult, Death
from ibidem.codetanks.server.commands import Idle
from ibidem.codetanks.server.vehicle import Armour, Missile
from ibidem.codetanks.server.world import World


DELTA = 0.000001


def to_point(p):
    return Point(p.x, p.y)


class Shared(object):
    bot_id = Id("bot", 1)
    initial_x = 30
    initial_y = 50
    initial_direction = Point2(1, 0)
    initial_turret = Point2(-1, 0)

    @classmethod
    def setup_class(cls):
        cls.world = create_autospec(World)
        cls.world.arena = Arena(500, 500)

    def setup(self):
        self.tank = self._create_tank()
        self.armour = Armour(self.tank, self.world)
        self.bullet = self._create_bullet()
        self.missile = Missile(self.bullet, self.world, self.armour)
        self.world.is_collision.return_value = False
        self.world.reset_mock()

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
    def test_armour_properties_reflect_tank(self):
        assert_that(self.armour.position.x, equal_to(self.tank.position.x))
        assert_that(self.armour.position.y, equal_to(self.tank.position.y))
        assert_that(self.armour.direction.x, equal_to(self.tank.direction.x))
        assert_that(self.armour.direction.y, equal_to(self.tank.direction.y))
        assert_that(self.armour.turret.x, equal_to(self.tank.turret.x))
        assert_that(self.armour.turret.y, equal_to(self.tank.turret.y))
        assert_that(self.armour.status, equal_to(self.tank.status))
        assert_that(self.armour.health, equal_to(self.tank.health))

    def test_missilie_properties_reflect_bullet(self):
        assert_that(self.missile.position.x,  equal_to(self.bullet.position.x))
        assert_that(self.missile.position.y,  equal_to(self.bullet.position.y))
        assert_that(self.missile.direction.x, equal_to(self.bullet.direction.x))
        assert_that(self.missile.direction.y, equal_to(self.bullet.direction.y))

    def test_setting_position_is_applied_to_entity(self):
        new_position = Point2(20, 40)
        for vehicle, entity in (self.armour, self.tank), (self.missile, self.bullet):
            vehicle.position = new_position
            assert_that(entity.position.x, equal_to(new_position.x))
            assert_that(entity.position.y, equal_to(new_position.y))

    def test_setting_direction_is_applied_to_entity(self):
        new_direction = Point2(1, -1)
        for vehicle, entity in (self.armour, self.tank), (self.missile, self.bullet):
            vehicle.direction = new_direction
            assert_that(entity.direction.x, equal_to(new_direction.x))
            assert_that(entity.direction.y, equal_to(new_direction.y))

    def test_setting_turret_is_applied_to_entity(self):
        new_turret = Point2(1, -1)
        self.armour.turret = new_turret
        assert_that(self.tank.turret.x, equal_to(new_turret.x))
        assert_that(self.tank.turret.y, equal_to(new_turret.y))

    def test_setting_status_is_applied_to_entity(self):
        status = BotStatus.MOVING
        self.armour.status = status
        assert_that(self.tank.status, equal_to(status))

    def test_inflicting_damage_is_applied_to_tank(self):
        self.armour.inflict(BULLET_DAMAGE, self.armour)
        assert_that(self.tank.health, equal_to(MAX_HEALTH - BULLET_DAMAGE))


class TestMove(Shared):
    def test_move_forwards(self):
        distance = 10
        target_x = self.initial_x + distance
        self.armour.move(distance)
        assert_that(self.armour.status, equal_to(BotStatus.MOVING))
        assert_that(self.armour.position.x, equal_to(self.initial_x))
        assert_that(self.armour.position.y, equal_to(self.initial_y))
        while self.armour.position.x < target_x:
            assert_that(self.armour.status, equal_to(BotStatus.MOVING))
            assert_that(self.armour.position.x, less_than(target_x))
            self.armour.update(random_ticks())
            assert_that(self.armour.position.x, greater_than(self.initial_x))
        assert_that(self.armour._command, instance_of(Idle))
        assert_that(self.armour.position.x, equal_to(target_x))
        assert_that(self.armour.position.y, equal_to(self.initial_y))

    def test_move_backwards_is_illegal(self):
        self.armour.move(-10)
        self.armour.update(random_ticks())
        assert_that(self.armour._command, instance_of(Idle))
        assert_that(self.armour.position.x, equal_to(self.initial_x))
        assert_that(self.armour.position.y, equal_to(self.initial_y))

    def test_world_is_checked_for_valid_position(self):
        self.armour.move(1)
        self.armour.update(10)
        self.world.is_collision.assert_called_once_with(self.armour)

    def test_world_is_checked_for_valid_position_for_missile(self):
        self.missile.update(random_ticks())
        self.world.is_collision.assert_called_once_with(self.missile)

    def test_vehicle_is_not_moved_if_new_position_invalid(self):
        self.world.is_collision.return_value = True
        self.missile.update(random_ticks())
        assert_that(self.missile.position.x, equal_to(self.initial_x))
        assert_that(self.missile.position.y, equal_to(self.initial_y))
        self.armour.move(100)
        self.armour.update(random_ticks())
        assert_that(self.armour.position.x, equal_to(self.initial_x))
        assert_that(self.armour.position.y, equal_to(self.initial_y))

    def test_missile_disappears_when_hitting_boundary(self):
        self.world.is_collision.return_value = True
        self.missile.update(random_ticks())
        self.world.remove_bullet.assert_called_with(self.missile)

    def test_missile_disappears_when_hitting_other_tank(self):
        self.world.is_collision.return_value = self.armour
        self.missile.update(random_ticks())
        self.world.remove_bullet.assert_called_with(self.missile)

    def test_missile_inflicts_damage_when_hitting_other_tank(self):
        self.world.is_collision.return_value = self.armour
        self.missile.update(random_ticks())
        assert_that(self.armour.health, equal_to(MAX_HEALTH - BULLET_DAMAGE))


class RotateAndAim(Shared):
    def _test(self, desc, angle, target_vector):
        self._act(angle)
        self._assert_starting_state()
        while self._continue(target_vector):
            self._assert_pre_update(target_vector)
            self.armour.update(random_ticks())
            self._assert_post_update(angle, target_vector)
        self._assert_ending_state(target_vector)

    def _act(self, angle):
        raise NotImplementedError

    def _assert_starting_state(self):
        expected_status = self._get_starting_status()
        assert_that(self.armour.status, equal_to(expected_status), "Starting status")
        expected_vector = self._get_starting_vector()
        assert_that_vector_matches(self._get_actual_vector(), expected_vector, equal_to(0.0), "Starting vectors")

    def _get_starting_status(self):
        raise NotImplementedError

    def _get_starting_vector(self):
        raise NotImplementedError

    def _continue(self, target_vector):
        raise NotImplementedError

    def _assert_pre_update(self, expected_vector):
        expected_status = self._get_pre_update_status()
        assert_that(self.armour.status, equal_to(expected_status), "Pre-update status")
        assert_that_vector_matches(self._get_actual_vector(), expected_vector, is_not(equal_to(0.0)), "Pre-update vectors")

    def _get_pre_update_status(self):
        raise NotImplementedError

    def _get_actual_vector(self):
        raise NotImplementedError

    def _assert_post_update(self, angle, target_vector):
        assert_that_vector_matches(self._get_actual_vector(), target_vector, less_than(abs(angle)), "Post-update vectors")

    def _assert_ending_state(self, target_vector):
        assert_that(self.armour._command, instance_of(Idle))
        assert_that_vector_matches(self._get_actual_vector(), target_vector, close_to(0.0, DELTA), "Ending vectors")


class TestRotate(RotateAndAim):
    def _get_starting_status(self):
        return BotStatus.ROTATING

    def _get_starting_vector(self):
        return self.initial_direction

    def _get_pre_update_status(self):
        return BotStatus.ROTATING

    def _get_actual_vector(self):
        return self.armour.direction

    def _continue(self, target_vector):
        angle = self.armour.direction.angle(target_vector)
        return not close_to(0.0, DELTA)._matches(angle)

    def _act(self, angle):
        self.armour.rotate(angle)

    def test_rotation(self):
        yield self._test, "anti-clockwise", 90, Vector2(0, 1)
        yield self._test, "clockwise", -90, Vector2(0, -1)


class TestAim(RotateAndAim):
    def _get_starting_status(self):
        return BotStatus.AIMING

    def _get_starting_vector(self):
        return self.initial_turret

    def _get_pre_update_status(self):
        return BotStatus.AIMING

    def _get_actual_vector(self):
        return self.armour.turret

    def _continue(self, target_vector):
        angle = self.armour.turret.angle(target_vector)
        return not close_to(0.0, DELTA)._matches(angle)

    def _act(self, angle):
        self.armour.aim(angle)

    def test_aim(self):
        yield self._test, "anti-clockwise", 90, Vector2(0, -1)
        yield self._test, "clockwise", -90, Vector2(0, 1)


class TestFire(Shared):
    def test_fire(self):
        self.armour.fire()
        self.armour.update(random_ticks())
        self.world.add_bullet.assert_called_with(self.armour)


class TestScan(Shared):
    def test_scan(self):
        scan_result = ScanResult([])
        self.world.scan.return_value = scan_result
        self.armour.scan(10)
        self.armour.update(random_ticks())
        self.world.add_event.assert_called_with(self.armour.tank_id, scan_result)

    def test_scan_above_90_degrees_is_ignored(self):
        self.armour.scan(91)
        self.armour.update(random_ticks())
        assert_that(self.world.scan.call_args_list, empty())


class TestCollide(Shared):
    def _collide_test(self, other, result):
        assert_that(self.armour.collide(other), equal_to(result))

    def _point_generator(self, modifier):
        yield Point(self.initial_x - modifier, self.initial_y)
        yield Point(self.initial_x + modifier, self.initial_y)
        yield Point(self.initial_x, self.initial_y - modifier)
        yield Point(self.initial_x, self.initial_y + modifier)

    def test_armour_overlap_with_armour_is_detected(self):
        modifiers = (2*TANK_RADIUS, (2*TANK_RADIUS-1), TANK_RADIUS, 1)
        for modifier in modifiers:
            for pos in self._point_generator(modifier):
                yield self._collide_test, Armour(self._create_tank(1, pos), self.world), True
        yield self._collide_test, Armour(self._create_tank(1, Point(self.initial_x, self.initial_y)), self.world), True

    def test_armour_overlap_with_missile_is_detected(self):
        modifiers = (2*BULLET_RADIUS, (2*BULLET_RADIUS-1), BULLET_RADIUS, 1)
        for modifier in modifiers:
            for pos in self._point_generator(modifier):
                yield self._collide_test, Missile(self._create_bullet(0, pos), self.world, None), True
            yield self._collide_test, Missile(self._create_bullet(0, Point(self.initial_x, self.initial_y)), self.world, None), True

    def test_armour_non_overlap_is_accepted(self):
        abs_modifiers = (2*TANK_RADIUS+1, 3*TANK_RADIUS)
        modifiers = list(chain(abs_modifiers, (-1*m for m in abs_modifiers)))
        for x in (self.initial_x + modifier for modifier in modifiers):
            for y in (self.initial_y + modifier for modifier in modifiers):
                yield self._collide_test, Armour(self._create_tank(1, Point(x, y)), self.world), False

    def test_missile_non_overlap_is_accepted(self):
        abs_modifiers = (TANK_RADIUS+BULLET_RADIUS+1, TANK_RADIUS+2*BULLET_RADIUS)
        modifiers = list(chain(abs_modifiers, (-1*m for m in abs_modifiers)))
        for x in (self.initial_x + modifier for modifier in modifiers):
            for y in (self.initial_y + modifier for modifier in modifiers):
                yield self._collide_test, Missile(self._create_bullet(0, Point(x, y)), self.world, None), False

    def test_vehicle_does_not_collide_with_self(self):
        assert_that(self.armour.collide(self.armour), equal_to(False))
        assert_that(self.missile.collide(self.missile), equal_to(False))

    def test_missile_does_not_collide_with_parent(self):
        assert_that(self.missile.collide(self.armour), equal_to(False))


class TestDeath(Shared):
    def test_health_goes_to_zero(self):
        self.tank.health = 5
        self.armour.inflict(5, self.armour)
        self.world.add_event.assert_called_with(None, Death(self.tank, self.tank))

    def test_death_is_not_sent_while_alive(self):
        self.tank.health = 10
        self.armour.inflict(5, self.armour)
        assert_that(self.world.add_event.call_args_list, empty())

    def test_state_is_set_to_dead_after_death(self):
        self.tank.health = 5
        self.armour.inflict(5, self.armour)
        assert_that(self.armour.status, equal_to())

def assert_that_vector_matches(actual, expected, matcher, reason=""):
    assert_that(actual.angle(expected), matcher, reason)


def random_ticks():
    return int(uniform(5.0, 15.0))


if __name__ == "__main__":
    import nose
    nose.main()
