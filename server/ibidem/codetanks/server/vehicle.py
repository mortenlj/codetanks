#!/usr/bin/env python
# -*- coding: utf-8

import logging
import math

from euclid import Circle, Point2, Vector2, Ray2

from ibidem.codetanks.domain.constants import TANK_SPEED, ROTATION, ROTATION_TOLERANCE, TANK_RADIUS
from ibidem.codetanks.domain.ttypes import Point, BotStatus


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

    def _reached_target_position(self, position):
        return self.target_ray.intersect(Circle(position, 1.0))

    def update(self, ticks):
        should_end = False
        distance = ticks * self.speed
        new_pos = self.vehicle.calculate_new_position(distance)
        if not self.vehicle.is_valid_position(new_pos):
            return True
        elif self._reached_target_position(new_pos):
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


class Vehicle(object):
    def __init__(self, entity, world):
        self.entity = entity
        self._world = world
        self._command = Idle(self)

    @property
    def position(self):
        return Point2(self.entity.position.x, self.entity.position.y)

    @position.setter
    def position(self, value):
        self.entity.position = Point(value.x, value.y)

    @property
    def direction(self):
        return Vector2(self.entity.direction.x, self.entity.direction.y)

    @direction.setter
    def direction(self, value):
        value.normalize()
        self.entity.direction = Point(value.x, value.y)

    @property
    def turret(self):
        return Vector2(self.entity.turret.x, self.entity.turret.y)

    @turret.setter
    def turret(self, value):
        value.normalize()
        self.entity.turret = Point(value.x, value.y)

    @property
    def status(self):
        return self.entity.status

    @status.setter
    def status(self, value):
        self.entity.status = value

    def is_valid_position(self, position):
        return self._world.is_valid_position(position, self)

    def calculate_new_position(self, distance):
        return self.position + (self.direction * distance)

    def calculate_new_direction(self, theta):
        new = self.direction.rotate(theta)
        new.normalize()
        return new

    def calculate_new_turret(self, theta):
        new = self.turret.rotate(theta)
        new.normalize()
        return new

    def collide(self, other_pos):
        pos = self.position
        xdistance = pos.x - other_pos.x
        ydistance = pos.y - other_pos.y
        squared = xdistance ** 2 + ydistance ** 2
        return squared <= (TANK_RADIUS*2) ** 2

    def update(self, ticks):
        should_end = self._command.update(ticks)
        if should_end:
            self._command = Idle(self)

    ###################################
    # Commands
    ###################################

    def move(self, distance):
        if distance < 0.0:
            return
        self._command = Move(self, TANK_SPEED, distance)

    def rotate(self, angle):
        theta = math.radians(angle)
        if abs(theta) < ROTATION_TOLERANCE:
            return
        self._command = Rotate(self, theta)

    def aim(self, angle):
        theta = math.radians(angle)
        if abs(theta) < ROTATION_TOLERANCE:
            return
        self._command = Aim(self, theta)


if __name__ == "__main__":
    pass
