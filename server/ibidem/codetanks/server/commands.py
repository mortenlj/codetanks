#!/usr/bin/env python
# -*- coding: utf-8

import logging

from euclid import Ray2, Circle

from ibidem.codetanks.domain.constants import ROTATION, ROTATION_TOLERANCE
from ibidem.codetanks.domain.ttypes import BotStatus


LOG = logging.getLogger(__name__)


class Idle(object):
    status = BotStatus.IDLE

    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.vehicle.status = self.status

    def update(self, ticks):
        return False


class Move(Idle):
    status = BotStatus.MOVING

    def __init__(self, vehicle, speed, distance):
        super(Move, self).__init__(vehicle)
        self.speed = speed
        self.target_ray = Ray2(vehicle.calculate_new_position(distance), vehicle.direction)
        LOG.debug("Moving to %r", self.target_ray)

    def _reached_target_position(self, position):
        return self.target_ray.intersect(Circle(position, 1.0))

    def update(self, ticks):
        should_end = False
        distance = ticks * self.speed
        LOG.debug("Attempting to move %r", distance)
        new_pos = self.vehicle.calculate_new_position(distance)
        LOG.debug("New position: %r", new_pos)
        if not self.vehicle.is_valid_position(new_pos):
            LOG.debug("Aborting move, new position is invalid")
            return True
        elif self._reached_target_position(new_pos):
            LOG.debug("Reached target %r", self.target_ray)
            new_pos = self.target_ray.p
            should_end = True
        self.vehicle.position = new_pos
        return should_end


class RotateAndAim(Idle):
    def __init__(self, vehicle, theta):
        super(RotateAndAim, self).__init__(vehicle)
        self.rotation = ROTATION if theta > 0.0 else -ROTATION
        self.target = self._calculate(theta)

    def _reached_target(self, direction):
        angle = self.target.angle(direction)
        LOG.debug("Angle between %r and %r is %r", self.target, direction, angle)
        return angle < ROTATION_TOLERANCE

    def update(self, ticks):
        should_end = False
        theta = ticks * self.rotation
        new = self._calculate(theta)
        if self._reached_target(new):
            new = self.target
            should_end = True
        self._update_vehicle(new)
        return should_end

    def _calculate(self, theta):
        raise NotImplementedError("This command must be subclassed")

    def _update_vehicle(self, new):
        raise NotImplementedError("This command must be subclassed")


class Rotate(RotateAndAim):
    status = BotStatus.ROTATING

    def _calculate(self, theta):
        return self.vehicle.calculate_new_direction(theta)

    def _update_vehicle(self, new):
        self.vehicle.direction = new


class Aim(RotateAndAim):
    status = BotStatus.AIMING

    def _calculate(self, theta):
        return self.vehicle.calculate_new_turret(theta)

    def _update_vehicle(self, new):
        self.vehicle.turret = new


class Fire(Idle):
    status = BotStatus.FIRING

    def __init__(self, vehicle, world):
        super(Fire, self).__init__(vehicle)
        self._world = world

    def update(self, ticks):
        self._world.add_bullet(self.vehicle)
        return True