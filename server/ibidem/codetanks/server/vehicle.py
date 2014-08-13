#!/usr/bin/env python
# -*- coding: utf-8

import logging
import math

from euclid import Point2, Vector2

from ibidem.codetanks.domain.constants import TANK_SPEED, ROTATION_TOLERANCE, TANK_RADIUS, BULLET_SPEED, BULLET_RADIUS
from ibidem.codetanks.domain.ttypes import Point
from ibidem.codetanks.server.commands import Idle, Move, Rotate, Aim, Fire


LOG = logging.getLogger(__name__)


class Vehicle(object):
    radius = None

    def __init__(self, entity, world):
        self.entity = entity
        self._world = world
        self._command = Idle(self)

    def calculate_new_position(self, distance):
        return self.position + (self.direction * distance)

    def collide(self, other):
        if other is self:
            return False
        pos = self.position
        other_pos = other.position
        xdistance = pos.x - other_pos.x
        ydistance = pos.y - other_pos.y
        squared = xdistance ** 2 + ydistance ** 2
        return squared <= (other.radius+self.radius) ** 2

    def update(self, ticks):
        should_end = self._command.update(ticks)
        if should_end:
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


class Armour(Vehicle):
    radius = TANK_RADIUS

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

    def is_valid_position(self):
        return self._world.is_valid_position(self)

    def calculate_new_direction(self, theta):
        new = self.direction.rotate(theta)
        new.normalize()
        return new

    def calculate_new_turret(self, theta):
        new = self.turret.rotate(theta)
        new.normalize()
        return new

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

    def fire(self):
        self._command = Fire(self, self._world)

    def __repr__(self):
        keys = ("entity", "position", "direction", "turret", "status")
        return "Armour(%s)" % ", ".join("%s=%r" % (key, getattr(self, key)) for key in keys)


class Missile(Vehicle):
    radius = BULLET_RADIUS

    def __init__(self, entity, world, parent):
        super(Missile, self).__init__(entity, world)
        self._parent = parent
        arena = world.arena
        LOG.debug("Missile %r created" % self)
        self._command = Move(self, BULLET_SPEED, arena.width + arena.height)

    def is_valid_position(self):
        return self._world.is_valid_position(self)

    def collide(self, other):
        if other is self._parent:
            return False
        return super(Missile, self).collide(other)

    def __repr__(self):
        keys = ("entity", "position", "direction")
        return "Missile(%s)" % ", ".join("%s=%r" % (key, getattr(self, key)) for key in keys)


if __name__ == "__main__":
    pass
