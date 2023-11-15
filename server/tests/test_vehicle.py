#!/usr/bin/env python
# -*- coding: utf-8

import pytest
from euclid import Point2, Vector2
from mock import create_autospec, call

from ibidem.codetanks.domain.messages_pb2 import Tank, Id, Point, BotStatus, Bullet, Arena, Death, Event, ScanComplete
from ibidem.codetanks.server.commands import Idle
from ibidem.codetanks.server.constants import TANK_RADIUS, BULLET_RADIUS, MAX_HEALTH, BULLET_DAMAGE
from ibidem.codetanks.server.vehicle import Armour, Missile
from ibidem.codetanks.server.world import World

TICKS = 5


def to_point(p):
    return Point(x=p.x, y=p.y)


@pytest.fixture
def world():
    world = create_autospec(World)
    world.arena = Arena(width=500, height=500)
    world.is_collision.return_value = False
    return world


class Shared(object):
    bot_id = Id(name="bot", version=1)
    initial_x = 30
    initial_y = 50
    initial_direction = Point2(1, 0)
    initial_turret = Point2(-1, 0)

    @pytest.fixture
    def tank(self):
        return self._create_tank()

    @pytest.fixture
    def armour(self, tank, world):
        return Armour(tank, world)

    @pytest.fixture
    def other(self, world):
        return Armour(self._create_tank(1, Point(x=250, y=250)), world)

    @pytest.fixture
    def bullet(self):
        return self._create_bullet()

    @pytest.fixture
    def missile(self, bullet, world, armour):
        return Missile(bullet, world, armour)

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
    def test_armour_properties_reflect_tank(self, armour, tank):
        assert armour.position.x == tank.position.x
        assert armour.position.y == tank.position.y
        assert armour.direction.x == tank.direction.x
        assert armour.direction.y == tank.direction.y
        assert armour.turret.x == tank.turret.x
        assert armour.turret.y == tank.turret.y
        assert armour.status == tank.status
        assert armour.health == tank.health

    def test_missilie_properties_reflect_bullet(self, missile, bullet):
        assert missile.position.x == bullet.position.x
        assert missile.position.y == bullet.position.y
        assert missile.direction.x == bullet.direction.x
        assert missile.direction.y == bullet.direction.y

    def test_setting_position_is_applied_to_entity(self, armour, tank, missile, bullet):
        new_position = Point2(20, 40)
        for vehicle, entity in (armour, tank), (missile, bullet):
            vehicle.position = new_position
            assert entity.position.x == new_position.x
            assert entity.position.y == new_position.y

    def test_setting_direction_is_applied_to_entity(self, armour, tank, missile, bullet):
        new_direction = Point2(1, -1)
        for vehicle, entity in (armour, tank), (missile, bullet):
            vehicle.direction = new_direction
            assert entity.direction.x == new_direction.x
            assert entity.direction.y == new_direction.y

    def test_setting_turret_is_applied_to_entity(self, armour, tank):
        new_turret = Point2(1, -1)
        armour.turret = new_turret
        assert tank.turret.x == new_turret.x
        assert tank.turret.y == new_turret.y

    def test_setting_status_is_applied_to_entity(self, armour, tank):
        status = BotStatus.MOVING
        armour.status = status
        assert tank.status == status

    def test_inflicting_damage_is_applied_to_tank(self, armour, tank):
        armour.inflict(BULLET_DAMAGE, armour)
        assert tank.health == MAX_HEALTH - BULLET_DAMAGE


class TestMove(Shared):
    def test_move_forwards(self, armour):
        distance = 10
        target_x = self.initial_x + distance
        armour.move(distance)
        assert armour.status == BotStatus.MOVING
        assert armour.position.x == self.initial_x
        assert armour.position.y == self.initial_y
        while armour.position.x < target_x:
            assert armour.status == BotStatus.MOVING
            assert armour.position.x < target_x
            armour.update(TICKS)
            assert armour.position.x > self.initial_x
        assert isinstance(armour._command, Idle)
        assert armour.position.x == target_x
        assert armour.position.y == self.initial_y

    def test_move_backwards_is_illegal(self, armour):
        armour.move(-10)
        armour.update(TICKS)
        assert isinstance(armour._command, Idle)
        assert armour.position.x == self.initial_x
        assert armour.position.y == self.initial_y

    def test_world_is_checked_for_valid_position(self, armour, world):
        armour.move(1)
        armour.update(10)
        world.is_collision.assert_called_once_with(armour)

    def test_world_is_checked_for_valid_position_for_missile(self, missile, world):
        missile.update(TICKS)
        world.is_collision.assert_called_once_with(missile)

    def test_vehicle_is_not_moved_if_new_position_invalid(self, world, armour, missile):
        world.is_collision.return_value = True
        missile.update(TICKS)
        assert missile.position.x == self.initial_x
        assert missile.position.y == self.initial_y
        armour.move(100)
        armour.update(TICKS)
        assert armour.position.x == self.initial_x
        assert armour.position.y == self.initial_y

    def test_missile_disappears_when_hitting_boundary(self, world, missile):
        world.is_collision.return_value = True
        missile.update(TICKS)
        world.remove_bullet.assert_called_with(missile)

    def test_missile_disappears_when_hitting_other_tank(self, world, missile, other):
        world.is_collision.return_value = other
        missile.update(TICKS)
        world.remove_bullet.assert_called_with(missile)

    def test_missile_inflicts_damage_when_hitting_other_tank(self, world, missile, other):
        world.is_collision.return_value = other
        missile.update(TICKS)
        assert other.health == MAX_HEALTH - BULLET_DAMAGE


class RotateAndAim(Shared):
    def _test(self, desc, angle, target_vector, armour):
        self._act(angle, armour)
        self._assert_starting_state(armour)
        count = 0
        while self._continue(target_vector, armour):
            self._assert_pre_update(target_vector, armour)
            armour.update(TICKS)
            count += 1
            self._assert_post_update(angle, target_vector, armour)
        self._assert_ending_state(target_vector, armour)
        assert count > 1

    def _act(self, angle, armour):
        raise NotImplementedError

    def _assert_starting_state(self, armour):
        expected_status = self._get_starting_status()
        assert armour.status == expected_status
        expected_vector = self._get_starting_vector()
        assert angle_difference(self._get_actual_vector(armour), expected_vector) == pytest.approx(0.0)

    def _get_starting_status(self):
        raise NotImplementedError

    def _get_starting_vector(self):
        raise NotImplementedError

    def _continue(self, target_vector, armour):
        raise NotImplementedError

    def _assert_pre_update(self, expected_vector, armour):
        expected_status = self._get_pre_update_status()
        assert armour.status == expected_status
        assert angle_difference(self._get_actual_vector(armour), expected_vector) != pytest.approx(0.0)

    def _get_pre_update_status(self):
        raise NotImplementedError

    def _get_actual_vector(self, armour):
        raise NotImplementedError

    def _assert_post_update(self, angle, target_vector, armour):
        assert angle_difference(self._get_actual_vector(armour), target_vector) < abs(angle)

    def _assert_ending_state(self, target_vector, armour):
        assert isinstance(armour._command, Idle)
        assert angle_difference(self._get_actual_vector(armour), target_vector) == pytest.approx(0.0)


class TestRotate(RotateAndAim):
    def _get_starting_status(self):
        return BotStatus.ROTATING

    def _get_starting_vector(self):
        return self.initial_direction

    def _get_pre_update_status(self):
        return BotStatus.ROTATING

    def _get_actual_vector(self, armour):
        return armour.direction

    def _continue(self, target_vector, armour):
        angle = armour.direction.angle(target_vector)
        return angle != pytest.approx(0.0)

    def _act(self, angle, armour):
        armour.rotate(angle)

    @pytest.mark.parametrize("angle, target_vector", (
            pytest.param(90, Vector2(0, 1), id="anti-clockwise"),
            pytest.param(-90, Vector2(0, -1), id="clockwise"),
    ))
    def test_rotation(self, angle, target_vector, armour):
        self._test("", angle, target_vector, armour)


class TestAim(RotateAndAim):
    def _get_starting_status(self):
        return BotStatus.AIMING

    def _get_starting_vector(self):
        return self.initial_turret

    def _get_pre_update_status(self):
        return BotStatus.AIMING

    def _get_actual_vector(self, armour):
        return armour.turret

    def _continue(self, target_vector, armour):
        angle = armour.turret.angle(target_vector)
        return angle != pytest.approx(0.0)

    def _act(self, angle, armour):
        armour.aim(angle)

    @pytest.mark.parametrize("angle, target_vector", (
            pytest.param(90, Vector2(0, -1), id="anti-clockwise"),
            pytest.param(-90, Vector2(0, 1), id="clockwise"),
    ))
    def test_aim(self, angle, target_vector, armour):
        self._test("", angle, target_vector, armour)


class TestFire(Shared):
    def test_fire(self, world, armour):
        armour.fire()
        armour.update(TICKS)
        world.add_bullet.assert_called_with(armour)


class TestScan(Shared):
    def test_scan(self, world, armour):
        scan_result = Event(scan_complete=ScanComplete(tanks=[], you=armour.entity))
        world.scan.return_value = []
        armour.scan(10)
        armour.update(TICKS)
        expected_calls = [
            call(armour.tank_id, scan_result),
        ]
        assert world.add_event.call_args_list == expected_calls

    def test_scan_above_90_degrees_is_ignored(self, world, armour):
        armour.scan(91)
        armour.update(TICKS)
        world.scan.assert_not_called()


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
    def test_armour_overlap_with_armour_is_detected(self, x_func, y_func, armour_modifier, world, armour):
        point = Point(x=x_func(self, armour_modifier), y=y_func(self, armour_modifier))
        other = Armour(self._create_tank(1, point), world)
        assert armour.collide(other)

    @pytest.mark.parametrize("x_func, y_func", (
            pytest.param(lambda s, m: s.initial_x - m, lambda s, m: s.initial_y, id="left_of"),
            pytest.param(lambda s, m: s.initial_x + m, lambda s, m: s.initial_y, id="right_of"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y - m, id="below"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y + m, id="above"),
            pytest.param(lambda s, m: s.initial_x, lambda s, m: s.initial_y, id="centered"),
    ))
    def test_armour_overlap_with_missile_is_detected(self, x_func, y_func, missile_modifier, world, armour):
        point = Point(x=x_func(self, missile_modifier), y=y_func(self, missile_modifier))
        other = Missile(self._create_bullet(0, point), world, None)
        assert armour.collide(other)

    @pytest.mark.parametrize("offset_vector, other_func", (
            pytest.param(Vector2(2 * TANK_RADIUS + 1, 0),
                         lambda s, x, y, w: Armour(s._create_tank(1, Point(x=x, y=y)), w),
                         id="armour_to_the_right"),
            pytest.param(Vector2(-2 * TANK_RADIUS + 1, 0),
                         lambda s, x, y, w: Armour(s._create_tank(1, Point(x=x, y=y)), w),
                         id="armour_to_the_left"),
            pytest.param(Vector2(0, 2 * TANK_RADIUS + 1),
                         lambda s, x, y, w: Armour(s._create_tank(1, Point(x=x, y=y)), w),
                         id="armour_above"),
            pytest.param(Vector2(0, -2 * TANK_RADIUS + 1),
                         lambda s, x, y, w: Armour(s._create_tank(1, Point(x=x, y=y)), w),
                         id="armour_below"),
            pytest.param(Vector2(2 * BULLET_RADIUS + 1, 0),
                         lambda s, x, y, w: Missile(s._create_bullet(1, Point(x=x, y=y)), w,
                                                    None), id="missile_to_the_right"),
            pytest.param(Vector2(-2 * BULLET_RADIUS + 1, 0),
                         lambda s, x, y, w: Missile(s._create_bullet(1, Point(x=x, y=y)), w,
                                                    None), id="missile_to_the_left"),
            pytest.param(Vector2(0, 2 * BULLET_RADIUS + 1),
                         lambda s, x, y, w: Missile(s._create_bullet(1, Point(x=x, y=y)), w,
                                                    None), id="missile_above"),
            pytest.param(Vector2(0, -2 * BULLET_RADIUS + 1),
                         lambda s, x, y, w: Missile(s._create_bullet(1, Point(x=x, y=y)), w,
                                                    None), id="missile_below"),
    ))
    def test_non_overlap_is_accepted(self, offset_vector, other_func, world, armour):
        other = other_func(self, offset_vector.x, offset_vector.y, world)
        assert not armour.collide(other)

    def test_vehicle_does_not_collide_with_self(self, armour, missile):
        assert not armour.collide(armour)
        assert not missile.collide(missile)

    def test_missile_does_not_collide_with_parent(self, armour, missile):
        missile.position = armour.position
        assert not missile.collide(armour)

    def test_missile_does_not_collide_with_dead_tank(self, missile, other):
        other.status = BotStatus.DEAD
        missile.position = other.position
        assert not missile.collide(other)


class TestDeath(Shared):
    def test_health_goes_to_zero(self, world, armour, tank):
        tank.health = 5
        armour.inflict(5, armour)
        world.add_event.assert_called_with(tank.id, Event(death=Death(victim=tank, perpetrator=tank)))

    def test_death_is_not_sent_while_alive(self, world, armour, tank):
        tank.health = 10
        armour.inflict(5, armour)
        world.add_event.assert_not_called()

    def test_state_is_set_to_dead_after_death(self, world, armour, tank):
        tank.health = 5
        armour.inflict(5, armour)
        assert armour.status == BotStatus.DEAD


def angle_difference(a, b):
    return a.angle(b)
