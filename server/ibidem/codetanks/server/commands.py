#!/usr/bin/env python
# -*- coding: utf-8

import logging
import operator

from euclid import Ray2, Circle

from ibidem.codetanks.domain.ttypes import BotStatus
from ibidem.codetanks.server.constants import ROTATION

LOG = logging.getLogger(__name__)


class Idle(object):
    status = BotStatus.IDLE

    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.vehicle.status = self.status

    def update(self, ticks):
        return False


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

    def update(self, ticks):
        should_end = False
        distance = ticks * self.speed
        LOG.debug("Attempting to move %r", distance)
        old_pos = self.vehicle.position
        new_pos = self.vehicle.calculate_new_position(distance)
        LOG.debug("New position: %r", new_pos)
        self.vehicle.position = new_pos
        if self.vehicle.is_collision():
            LOG.debug("Aborting move, new position is invalid")
            self.vehicle.position = old_pos
            return True
        elif self._reached_target_position(new_pos):
            LOG.debug("Reached target %r", self.target_ray)
            self.vehicle.position = self.target_ray.p
            should_end = True
        return should_end


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
                  self.target.angle(current),
                  self.operation)

    def _set_rotation(self):
        self.rotation = -ROTATION if self._get_current().clockwise(self.target) else ROTATION

    def _set_operation(self):
        self.operation = operator.gt if self.rotation > 0.0 else operator.lt

    def _reached_target(self, direction):
        angle = self.target.angle(direction)
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
        return should_end

    def _calculate(self, theta):
        raise NotImplementedError("This command must be subclassed")

    def _update_vehicle(self, new):
        raise NotImplementedError("This command must be subclassed")

    def _get_current(self):
        raise NotImplementedError("This command must be subclassed")


class Rotate(RotateAndAim):
    status = BotStatus.ROTATING

    def _calculate(self, theta):
        return self.vehicle.calculate_new_direction(theta)

    def _update_vehicle(self, new):
        self.vehicle.direction = new

    def _get_current(self):
        return self.vehicle.direction


class Aim(RotateAndAim):
    status = BotStatus.AIMING

    def _calculate(self, theta):
        return self.vehicle.calculate_new_turret(theta)

    def _update_vehicle(self, new):
        self.vehicle.turret = new

    def _get_current(self):
        return self.vehicle.turret


class Fire(Idle):
    status = BotStatus.FIRING

    def __init__(self, vehicle, world):
        super(Fire, self).__init__(vehicle)
        self._world = world

    def update(self, ticks):
        self._world.add_bullet(self.vehicle)
        return True


class Scan(Idle):
    status = BotStatus.SCANNING

    def __init__(self, vehicle, world, theta):
        super(Scan, self).__init__(vehicle)
        self._world = world
        self._theta = theta

    def update(self, ticks):
        scan_ray = Ray2(self.vehicle.position, self.vehicle.turret)
        result = self._world.scan(scan_ray, self._theta)
        self._world.add_event(self.vehicle.tank_id, result)
        return True
