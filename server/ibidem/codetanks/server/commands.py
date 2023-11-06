#!/usr/bin/env python
# -*- coding: utf-8

import logging
import operator

from euclid import Ray2, Circle

from ibidem.codetanks.domain.messages_pb2 import BotStatus, MovementComplete, RotationComplete, AimingComplete, \
    ShotFired, ScanComplete, Event
from ibidem.codetanks.server.constants import ROTATION, CANNON_RELOAD

LOG = logging.getLogger(__name__)


class Idle(object):
    status = BotStatus.IDLE

    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.vehicle.status = self.status

    def update(self, ticks):
        """Performs update and returns command and event"""
        return self, None


class Dead(Idle):
    status = BotStatus.DEAD


class Move(Idle):
    status = BotStatus.MOVING

    def __init__(self, vehicle, speed, distance):
        super(Move, self).__init__(vehicle)
        self.speed = speed
        LOG.debug("Starting move of %r", vehicle)
        target_position = vehicle.calculate_new_position(distance)
        LOG.debug("Calculated target_position: %r", target_position)
        self.target_ray = Ray2(target_position, vehicle.direction)
        LOG.debug("Moving to %r", self.target_ray)

    def _reached_target_position(self, position):
        return self.target_ray.intersect(Circle(position, 1.0))

    def _completion(self):
        if self.vehicle.is_tank():
            return Idle(self.vehicle), Event(movement_complete=MovementComplete(you=self.vehicle.entity))
        else:
            return Idle(self.vehicle), None

    def update(self, ticks):
        distance = ticks * self.speed
        LOG.debug("Attempting to move %r", distance)
        old_pos = self.vehicle.position
        new_pos = self.vehicle.calculate_new_position(distance)
        LOG.debug("New position: %r", new_pos)
        self.vehicle.position = new_pos
        if self.vehicle.is_collision():
            LOG.debug("Aborting move, new position is invalid")
            self.vehicle.position = old_pos
            return self._completion()
        elif self._reached_target_position(new_pos):
            LOG.debug("Reached target %r", self.target_ray)
            self.vehicle.position = self.target_ray.p
            return self._completion()
        return self, None


class RotateAndAim(Idle):
    def __init__(self, vehicle, theta):
        super(RotateAndAim, self).__init__(vehicle)
        self.target = self._calculate(theta)
        self._set_rotation()
        self._set_operation()
        current = self._get_current()
        LOG.debug("Starting to %r by %r from %r towards %r (current angle %r) until angle is %r 0.0",
                  self.__class__.__name__,
                  self.rotation,
                  current,
                  self.target,
                  self.target.angle_oriented(current),
                  self.operation)

    def _set_rotation(self):
        self.rotation = -ROTATION if self._get_current().angle_oriented(self.target) < 0 else ROTATION

    def _set_operation(self):
        self.operation = operator.gt if self.rotation > 0.0 else operator.lt

    def _reached_target(self, direction):
        angle = self.target.angle_oriented(direction)
        LOG.debug("Angle between %r and %r is %r", self.target, direction, angle)
        return self.operation(angle, 0.0)

    def update(self, ticks):
        should_end = False
        theta = ticks * self.rotation
        new = self._calculate(theta)
        if self._reached_target(new):
            LOG.debug("Reached target %r", self.target)
            new = self.target
            should_end = True
        self._update_vehicle(new)
        if should_end:
            return Idle(self.vehicle), self._completion_event()
        return self, None

    def _calculate(self, theta):
        raise NotImplementedError("This command must be subclassed")

    def _update_vehicle(self, new):
        raise NotImplementedError("This command must be subclassed")

    def _get_current(self):
        raise NotImplementedError("This command must be subclassed")

    def _completion_event(self):
        raise NotImplementedError("This command must be subclassed")


class Rotate(RotateAndAim):
    status = BotStatus.ROTATING

    def _calculate(self, theta):
        return self.vehicle.calculate_new_direction(theta)

    def _update_vehicle(self, new):
        self.vehicle.direction = new

    def _get_current(self):
        return self.vehicle.direction

    def _completion_event(self):
        return Event(rotation_complete=RotationComplete(you=self.vehicle.entity))


class Aim(RotateAndAim):
    status = BotStatus.AIMING

    def _calculate(self, theta):
        return self.vehicle.calculate_new_turret(theta)

    def _update_vehicle(self, new):
        self.vehicle.turret = new

    def _get_current(self):
        return self.vehicle.turret

    def _completion_event(self):
        return Event(aiming_complete=AimingComplete(you=self.vehicle.entity))


class Fire(Idle):
    status = BotStatus.FIRING

    def __init__(self, vehicle, world, bullet_speed):
        super(Fire, self).__init__(vehicle)
        self._world = world
        self._delay = bullet_speed * CANNON_RELOAD
        self._fired = False

    def update(self, ticks):
        if not self._fired:
            LOG.debug("Shot fired. Remaining delay: %f, ticks: %f", self._delay, ticks)
            self._world.add_bullet(self.vehicle)
            self._fired = True
            return self, None
        self._delay -= ticks
        if self._delay > 0:
            LOG.debug("Reload still in progress. Remaining delay: %f, ticks: %f", self._delay, ticks)
            return self, None
        return Idle(self.vehicle), Event(shot_fired=ShotFired(you=self.vehicle.entity))


class Scan(Idle):
    status = BotStatus.SCANNING

    def __init__(self, vehicle, world, theta):
        super(Scan, self).__init__(vehicle)
        self._world = world
        self._theta = theta

    def update(self, ticks):
        scan_ray = Ray2(self.vehicle.position, self.vehicle.turret)
        hits = self._world.scan(scan_ray, self._theta)
        return Idle(self.vehicle), Event(scan_complete=ScanComplete(tanks=hits, you=self.vehicle.entity))
