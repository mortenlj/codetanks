#!/usr/bin/env python
# -*- coding: utf-8
from random import uniform

import pytest
from euclid import Point2, Vector2
from mock import create_autospec, call

from ibidem.codetanks.domain.messages_pb2 import Tank, Id, Point, BotStatus, Bullet, Arena, ScanResult, Death, Event, \
    CommandResult
from ibidem.codetanks.server.commands import Idle
from ibidem.codetanks.server.constants import TANK_RADIUS, BULLET_RADIUS, MAX_HEALTH, BULLET_DAMAGE
from ibidem.codetanks.server.vehicle import Armour, Missile
from ibidem.codetanks.server.world import World

DELTA = 0.000001


def to_point(p):
    return Point(x=p.x, y=p.y)


class Shared(object):
    bot_id = Id(name="bot", version=1)
    initial_x = 30
    initial_y = 50
    initial_direction = Point2(1, 0)
    initial_turret = Point2(-1, 0)

    @classmethod
    def setup_class(cls):
        cls.world = create_autospec(World)
        cls.world.arena = Arena(width=500, height=500)

    def setup(self):
        self.tank = self._create_tank()
        self.armour = Armour(self.tank, self.world)
        self.other = Armour(self._create_tank(1, Point(x=250, y=250)), self.world)
        self.bullet = self._create_bullet()
        self.missile = Missile(self.bullet, self.world, self.armour)
        self.world.is_collision.return_value = False
        self.world.reset_mock()

    def _create_tank(self, tank_id=0, position=None):
        if position is None:
            position = Point(x=self.initial_x, y=self.initial_y)
        return Tank(
            id=tank_id,
            bot_id=self.bot_id,
            position=position,
            direction=to_point(self.initial_direction),
            turret=to_point(self.initial_turret),
            health=MAX_HEALTH,
            status=BotStatus.IDLE
        )

    def _create_bullet(self, bullet_id=0, position=None):
        if position is None:
            position = Point(x=self.initial_x, y=self.initial_y)
        return Bullet(
            id=bullet_id,
            position=position,
            direction=to_point(self.initial_direction)
        )


class TestVehicle(Shared):
    def test_armour_properties_reflect_tank(self):
        assert self.armour.position.x == self.tank.position.x
        assert self.armour.position.y == self.tank.position.y
        assert self.armour.direction.x == self.tank.direction.x
        assert self.armour.direction.y == self.tank.direction.y
        assert self.armour.turret.x == self.tank.turret.x
        assert self.armour.turret.y == self.tank.turret.y
        assert self.armour.status == self.tank.status
        assert self.armour.health == self.tank.health

    def test_missilie_properties_reflect_bullet(self):
        assert self.missile.position.x == self.bullet.position.x
        assert self.missile.position.y == self.bullet.position.y
        assert self.missile.direction.x == self.bullet.direction.x
        assert self.missile.direction.y == self.bullet.direction.y

    def test_setting_position_is_applied_to_entity(self):
        new_position = Point2(20, 40)
        for vehicle, entity in (self.armour, self.tank), (self.missile, self.bullet):
            vehicle.position = new_position
            assert entity.position.x == new_position.x
            assert entity.position.y == new_position.y

    def test_setting_direction_is_applied_to_entity(self):
        new_direction = Point2(1, -1)
        for vehicle, entity in (self.armour, self.tank), (self.missile, self.bullet):
            vehicle.direction = new_direction
            assert entity.direction.x == new_direction.x
            assert entity.direction.y == new_direction.y

    def test_setting_turret_is_applied_to_entity(self):
        new_turret = Point2(1, -1)
        self.armour.turret = new_turret
        assert self.tank.turret.x == new_turret.x
        assert self.tank.turret.y == new_turret.y

    def test_setting_status_is_applied_to_entity(self):
        status = BotStatus.MOVING
        self.armour.status = status
        assert self.tank.status == status

    def test_inflicting_damage_is_applied_to_tank(self):
        self.armour.inflict(BULLET_DAMAGE, self.armour)
        assert self.tank.health == MAX_HEALTH - BULLET_DAMAGE


class TestMove(Shared):
    def test_move_forwards(self):
        distance = 10
        target_x = self.initial_x + distance
        self.armour.move(distance)
        assert self.armour.status == BotStatus.MOVING
        assert self.armour.position.x == self.initial_x
        assert self.armour.position.y == self.initial_y
        while self.armour.position.x < target_x:
            assert self.armour.status == BotStatus.MOVING
            assert self.armour.position.x < target_x
            self.armour.update(random_ticks())
            assert self.armour.position.x > self.initial_x
        assert isinstance(self.armour._command, Idle)
        assert self.armour.position.x == target_x
        assert self.armour.position.y == self.initial_y

    def test_move_backwards_is_illegal(self):
        self.armour.move(-10)
        self.armour.update(random_ticks())
        assert isinstance(self.armour._command, Idle)
        assert self.armour.position.x == self.initial_x
        assert self.armour.position.y == self.initial_y

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
        assert self.missile.position.x == self.initial_x
        assert self.missile.position.y == self.initial_y
        self.armour.move(100)
        self.armour.update(random_ticks())
        assert self.armour.position.x == self.initial_x
        assert self.armour.position.y == self.initial_y

    def test_missile_disappears_when_hitting_boundary(self):
        self.world.is_collision.return_value = True
        self.missile.update(random_ticks())
        self.world.remove_bullet.assert_called_with(self.missile)

    def test_missile_disappears_when_hitting_other_tank(self):
        self.world.is_collision.return_value = self.other
        self.missile.update(random_ticks())
        self.world.remove_bullet.assert_called_with(self.missile)

    def test_missile_inflicts_damage_when_hitting_other_tank(self):
        self.world.is_collision.return_value = self.other
        self.missile.update(random_ticks())
        assert self.other.health == MAX_HEALTH - BULLET_DAMAGE


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
        assert self.armour.status == expected_status
        expected_vector = self._get_starting_vector()
        assert angle_difference(self._get_actual_vector(), expected_vector) == pytest.approx(0.0)

    def _get_starting_status(self):
        raise NotImplementedError

    def _get_starting_vector(self):
        raise NotImplementedError

    def _continue(self, target_vector):
        raise NotImplementedError

    def _assert_pre_update(self, expected_vector):
        expected_status = self._get_pre_update_status()
        assert self.armour.status == expected_status
        assert angle_difference(self._get_actual_vector(), expected_vector) != pytest.approx(0.0)

    def _get_pre_update_status(self):
        raise NotImplementedError

    def _get_actual_vector(self):
        raise NotImplementedError

    def _assert_post_update(self, angle, target_vector):
        assert angle_difference(self._get_actual_vector(), target_vector) < abs(angle)

    def _assert_ending_state(self, target_vector):
        assert isinstance(self.armour._command, Idle)
        assert angle_difference(self._get_actual_vector(), target_vector) == pytest.approx(0.0)


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
        return angle != pytest.approx(0.0)

    def _act(self, angle):
        self.armour.rotate(angle)

    @pytest.mark.parametrize("angle, target_vector", (
            pytest.param(90, Vector2(0, 1), id="anti-clockwise"),
            pytest.param(-90, Vector2(0, -1), id="clockwise"),
    ))
    def test_rotation(self, angle, target_vector):
        self._test("", angle, target_vector)


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
        return angle != pytest.approx(0.0)

    def _act(self, angle):
        self.armour.aim(angle)

    @pytest.mark.parametrize("angle, target_vector", (
            pytest.param(90, Vector2(0, -1), id="anti-clockwise"),
            pytest.param(-90, Vector2(0, 1), id="clockwise"),
    ))
    def test_aim(self, angle, target_vector):
        self._test("", angle, target_vector)


class TestFire(Shared):
    def test_fire(self):
        self.armour.fire()
        self.armour.update(random_ticks())
        self.world.add_bullet.assert_called_with(self.armour)


class TestScan(Shared):
    def test_scan(self):
        scan_result = Event(scan=ScanResult(tanks=[]))
        self.world.scan.return_value = scan_result
        self.armour.scan(10)
        self.armour.update(random_ticks())
        expected_calls = [
            call(self.armour.tank_id, scan_result),
            call(self.armour.tank_id, Event(result=CommandResult.COMPLETED))
        ]
        assert self.world.add_event.call_args_list == expected_calls

    def test_scan_above_90_degrees_is_ignored(self):
        self.armour.scan(91)
        self.armour.update(random_ticks())
        self.world.scan.assert_not_called()


class TestCollide(Shared):
    @pytest.fixture(params=(2 * TANK_RADIUS, (2 * TANK_RADIUS - 1), TANK_RADIUS, 1))
    def armour_modifier(self, request):
        return request.param

    @pytest.fixture(params=(2 * BULLET_RADIUS, (2 * BULLET_RADIUS - 1), BULLET_RADIUS, 1))
    def missile_modifier(self, request):
        return request.param

    @pytest.mark.parametrize("x_func, y_func", (
            pytest.param(lambda s, m: s.initial_x - m, lambda s, m: s.initial_y, id="left_of"),
            pytest.param(lambda s, m: s.initial_x + m, lambda s, m: s.initial_y, id="right_of"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y - m, id="below"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y + m, id="above"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y, id="centered"),
    ))
    def test_armour_overlap_with_armour_is_detected(self, x_func, y_func, armour_modifier):
        point = Point(x=x_func(self, armour_modifier), y=y_func(self, armour_modifier))
        other = Armour(self._create_tank(1, point), self.world)
        assert self.armour.collide(other)

    @pytest.mark.parametrize("x_func, y_func", (
            pytest.param(lambda s, m: s.initial_x - m, lambda s, m: s.initial_y, id="left_of"),
            pytest.param(lambda s, m: s.initial_x + m, lambda s, m: s.initial_y, id="right_of"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y - m, id="below"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y + m, id="above"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y, id="centered"),
    ))
    def test_armour_overlap_with_missile_is_detected(self, x_func, y_func, missile_modifier):
        point = Point(x=x_func(self, missile_modifier), y=y_func(self, missile_modifier))
        other = Missile(self._create_bullet(0, point), self.world, None)
        assert self.armour.collide(other)

    @pytest.mark.parametrize("offset_vector, other_func", (
            pytest.param(Vector2(2 * TANK_RADIUS + 1, 0),
                         lambda s, x, y: Armour(s._create_tank(1, Point(x=x, y=y)), s.world),
                         id="armour_to_the_right"),
            pytest.param(Vector2(-2 * TANK_RADIUS + 1, 0),
                         lambda s, x, y: Armour(s._create_tank(1, Point(x=x, y=y)), s.world),
                         id="armour_to_the_left"),
            pytest.param(Vector2(0, 2 * TANK_RADIUS + 1),
                         lambda s, x, y: Armour(s._create_tank(1, Point(x=x, y=y)), s.world),
                         id="armour_above"),
            pytest.param(Vector2(0, -2 * TANK_RADIUS + 1),
                         lambda s, x, y: Armour(s._create_tank(1, Point(x=x, y=y)), s.world),
                         id="armour_below"),
            pytest.param(Vector2(2 * BULLET_RADIUS + 1, 0),
                         lambda s, x, y: Missile(s._create_bullet(1, Point(x=x, y=y)), s.world,
                                                 None), id="missile_to_the_right"),
            pytest.param(Vector2(-2 * BULLET_RADIUS + 1, 0),
                         lambda s, x, y: Missile(s._create_bullet(1, Point(x=x, y=y)), s.world,
                                                 None), id="missile_to_the_left"),
            pytest.param(Vector2(0, 2 * BULLET_RADIUS + 1),
                         lambda s, x, y: Missile(s._create_bullet(1, Point(x=x, y=y)), s.world,
                                                 None), id="missile_above"),
            pytest.param(Vector2(0, -2 * BULLET_RADIUS + 1),
                         lambda s, x, y: Missile(s._create_bullet(1, Point(x=x, y=y)), s.world,
                                                 None), id="missile_below"),
    ))
    def test_non_overlap_is_accepted(self, offset_vector, other_func):
        other = other_func(self, offset_vector.x, offset_vector.y)
        assert not self.armour.collide(other)

    def test_vehicle_does_not_collide_with_self(self):
        assert not self.armour.collide(self.armour)
        assert not self.missile.collide(self.missile)

    def test_missile_does_not_collide_with_parent(self):
        self.missile.position = self.armour.position
        assert not self.missile.collide(self.armour)

    def test_missile_does_not_collide_with_dead_tank(self):
        self.other.status = BotStatus.DEAD
        self.missile.position = self.other.position
        assert not self.missile.collide(self.other)


class TestDeath(Shared):
    def test_health_goes_to_zero(self):
        self.tank.health = 5
        self.armour.inflict(5, self.armour)
        self.world.add_event.assert_called_with(None, Event(death=Death(victim=self.tank, perpetrator=self.tank)))

    def test_death_is_not_sent_while_alive(self):
        self.tank.health = 10
        self.armour.inflict(5, self.armour)
        self.world.add_event.assert_not_called()

    def test_state_is_set_to_dead_after_death(self):
        self.tank.health = 5
        self.armour.inflict(5, self.armour)
        assert self.armour.status == BotStatus.DEAD


def angle_difference(a, b):
    return a.angle(b)


def random_ticks():
    return int(uniform(5.0, 15.0))
