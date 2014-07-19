#!/usr/bin/env python
# -*- coding: utf-8

import logging

from euclid import Circle, Point2, Vector2, Ray2

from ibidem.codetanks.domain.constants import TANK_SPEED, TANK_ROTATION, TANK_ROTATION_TOLERANCE
from ibidem.codetanks.domain.ttypes import Point, BotStatus


LOG = logging.getLogger(__name__)


class Vehicle(object):
    class _Meta(object):
        __slots__ = [
            # Targets
            'target_ray',
            'target_direction',

            # Motion properties
            'speed',
            'rotation'
        ]

        def __init__(self):
            self.target_ray = None
            self.target_direction = None
            self.speed = 0.0
            self.rotation = 0

        def reached_target_position(self, position):
            return self.target_ray.intersect(Circle(position, 1.0))

        def reached_target_direction(self, direction):
            angle = self.target_direction.angle(direction)
            LOG.debug("Angle between %r and %r is %r", self.target_direction, direction, angle)
            return angle < TANK_ROTATION_TOLERANCE

    def __init__(self, entity):
        self.entity = entity
        self._meta = Vehicle._Meta()

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
    def status(self):
        return self.entity.status

    def _calculate_new_position(self, distance):
        return self.position + (self.direction * distance)

    ################################
    # Update funcs
    ################################

    def update(self, ticks):
        {
            BotStatus.IDLE:     lambda ticks: ticks,
            BotStatus.MOVING:   self._update_position,
            BotStatus.ROTATING: self._update_direction
        }[self.status](ticks)

    def _update_position(self, ticks):
        distance = ticks * self._meta.speed
        new_pos = self._calculate_new_position(distance)
        if self._meta.reached_target_position(new_pos):
            new_pos = self._meta.target_ray.p
            self.entity.status = BotStatus.IDLE
        self.position = new_pos

    def _update_direction(self, ticks):
        LOG.debug("Updating direction by %r ticks", ticks)
        theta = ticks * self._meta.rotation
        LOG.debug("Rotating from direction %r by %r radians", self.direction, theta)
        new_direction = self.direction.rotate(theta)
        LOG.debug("New direction is %r", new_direction)
        if self._meta.reached_target_direction(new_direction):
            LOG.debug("New direction considered reaching target")
            new_direction = self._meta.target_direction
            self.entity.status = BotStatus.IDLE
        self.direction = new_direction
        LOG.debug("Set direction to %r", self.direction)

    ###################################
    # Commands
    ###################################

    def move(self, distance):
        if distance < 0.0:
            return
        new_pos = self._calculate_new_position(distance)
        self._meta.target_ray = Ray2(new_pos, self.direction)
        self._meta.speed = TANK_SPEED
        self.entity.status = BotStatus.MOVING

    def rotate(self, theta):
        if abs(theta) < TANK_ROTATION_TOLERANCE:
            return
        new_direction = self.direction.rotate(theta)
        new_direction.normalize()
        self._meta.target_direction = new_direction
        self._meta.rotation = TANK_ROTATION if theta > 0.0 else -TANK_ROTATION
        self.entity.status = BotStatus.ROTATING


if __name__ == "__main__":
    pass
