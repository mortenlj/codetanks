#!/usr/bin/env python
# -*- coding: utf-8

from euclid import Circle, Point2, Vector2, Ray2
from ibidem.codetanks.domain.constants import TANK_SPEED

from ibidem.codetanks.domain.ttypes import Point


class Vehicle(object):
    class _Meta(object):
        __slots__ = [
            'target_ray',
            'speed'
        ]

        def __init__(self):
            self.speed = 0.0
            self.target_ray = None

        def reached_target(self, position):
            return self.target_ray.intersect(Circle(position, 1.0))

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

    def move(self, distance):
        if distance < 0.0:
            return
        new_pos = self._calculate_new_position(distance)
        self._meta.target_ray = Ray2(new_pos, self.direction)
        self._meta.speed = TANK_SPEED

    def _calculate_new_position(self, distance):
        return self.position + (self.direction * distance)

    def update_position(self, ticks):
        if self._meta.target_ray:
            distance = ticks * self._meta.speed
            new_pos = self._calculate_new_position(distance)
            if self._meta.reached_target(new_pos):
                new_pos = self._meta.target_ray.p
                self._meta.speed = 0.0
            self.position = new_pos

if __name__ == "__main__":
    pass
