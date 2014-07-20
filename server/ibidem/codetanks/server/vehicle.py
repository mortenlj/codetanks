#!/usr/bin/env python
# -*- coding: utf-8

import logging

from euclid import Circle, Point2, Vector2, Ray2

from ibidem.codetanks.domain.constants import TANK_SPEED, ROTATION, ROTATION_TOLERANCE
from ibidem.codetanks.domain.ttypes import Point, BotStatus


LOG = logging.getLogger(__name__)


class Idle(object):
    status = BotStatus.IDLE

    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.vehicle.status = self.status

    def update(self, ticks):
        pass


class Move(Idle):
    status = BotStatus.MOVING

    def __init__(self, vehicle, speed, distance):
        super(Move, self).__init__(vehicle)
        self.speed = speed
        self.target_ray = Ray2(vehicle.calculate_new_position(distance), vehicle.direction)

    def _reached_target_position(self, position):
        return self.target_ray.intersect(Circle(position, 1.0))

    def update(self, ticks):
        distance = ticks * self.speed
        new_pos = self.vehicle.calculate_new_position(distance)
        if self._reached_target_position(new_pos):
            new_pos = self.target_ray.p
            self.vehicle.status = BotStatus.IDLE
        self.vehicle.position = new_pos


class Rotate(Idle):
    status = BotStatus.ROTATING

    def __init__(self, vehicle, theta):
        super(Rotate, self).__init__(vehicle)
        self.target_direction = vehicle.calculate_new_direction(theta)
        self.rotation = ROTATION if theta > 0.0 else -ROTATION

    def _reached_target_direction(self, direction):
        angle = self.target_direction.angle(direction)
        LOG.debug("Angle between %r and %r is %r", self.target_direction, direction, angle)
        return angle < ROTATION_TOLERANCE

    def update(self, ticks):
        LOG.debug("Updating direction by %r ticks", ticks)
        theta = ticks * self.rotation
        LOG.debug("Rotating from direction %r by %r radians", self.vehicle.direction, theta)
        new_direction = self.vehicle.calculate_new_direction(theta)
        LOG.debug("New direction is %r", new_direction)
        if self._reached_target_direction(new_direction):
            LOG.debug("New direction considered reaching target")
            new_direction = self.target_direction
            self.vehicle.status = BotStatus.IDLE
        self.vehicle.direction = new_direction
        LOG.debug("Set direction to %r", self.vehicle.direction)


class Aim(Idle):
    status = BotStatus.AIMING

    def __init__(self, vehicle, theta):
        super(Aim, self).__init__(vehicle)
        self.target_turret = vehicle.calculate_new_turret(theta)
        self.aiming = ROTATION if theta > 0.0 else -ROTATION

    def _reached_target_turret(self, turret):
        angle = self.target_turret.angle(turret)
        LOG.debug("Angle between %r and %r is %r", self.target_turret, turret, angle)
        return angle < ROTATION_TOLERANCE

    def update(self, ticks):
        LOG.debug("Updating turret by %r ticks", ticks)
        theta = ticks * self.aiming
        LOG.debug("Aiming from turret %r by %r radians", self.vehicle.turret, theta)
        new_turret = self.vehicle.turret.rotate(theta)
        LOG.debug("New turret is %r", new_turret)
        if self._reached_target_turret(new_turret):
            LOG.debug("New turret considered reaching target")
            new_turret = self.target_turret
            self.vehicle.status = BotStatus.IDLE
        self.vehicle.turret = new_turret
        LOG.debug("Set turret to %r", self.vehicle.turret)


class Vehicle(object):
    def __init__(self, entity):
        self.entity = entity
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

    def update(self, ticks):
        self._command.update(ticks)

    ###################################
    # Commands
    ###################################

    def move(self, distance):
        if distance < 0.0:
            return
        self._command = Move(self, TANK_SPEED, distance)

    def rotate(self, theta):
        if abs(theta) < ROTATION_TOLERANCE:
            return
        self._command = Rotate(self, theta)

    def aim(self, theta):
        if abs(theta) < ROTATION_TOLERANCE:
            return
        self._command = Aim(self, theta)


if __name__ == "__main__":
    pass
