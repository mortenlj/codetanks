#!/usr/bin/env python
# -*- coding: utf-8

from random import randint, uniform

from euclid import Vector2, Ray2, Point2, Circle

from ibidem.codetanks.domain.constants import TANK_SPEED
from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point


class _Meta(object):
    __slots__ = [
        'target_ray',
        'speed'
    ]


class _Wrapper(object):
    def __init__(self, entity):
        self.entity = entity
        self.meta = _Meta()


class World(object):
    arena = Arena()

    def __init__(self, world_width, world_height):
        self.arena = Arena(world_width, world_height)
        self._bullets = []
        self._tanks = []

    def add_tank(self, bot):
        tank = _Wrapper(Tank(
            bot.tank_id,
            bot.bot_id,
            self._select_valid_position(),
            self._select_random_direction(),
            self._select_random_direction()
        ))
        self._tanks.append(tank)

    @property
    def gamedata(self):
        return GameData(self.bullets, self.tanks)

    @property
    def tanks(self):
        return [w.entity for w in self._tanks]

    @property
    def bullets(self):
        return [w.entity for w in self._bullets]

    def _select_valid_position(self):
        return Point(randint(0, self.arena.width), randint(0, self.arena.height))

    def _select_random_direction(self):
        return Point(uniform(-1, 1), uniform(-1, 1))

    def update(self, ticks):
        for tank_wrapper in self._tanks:
            self._update_position(ticks, tank_wrapper)

    def _update_position(self, ticks, wrapper):
        meta = wrapper.meta
        entity = wrapper.entity
        old_pos = Point2(entity.position.x, entity.position.y)
        direction = Vector2(entity.direction.x, entity.direction.y)
        distance = ticks * meta.speed
        new_pos = old_pos + (direction * distance)
        if meta.target_ray.intersect(Circle(new_pos, 15.0)):
            new_pos = meta.target_ray.p
            meta.speed = 0.0
        entity.position = Point(new_pos.x, new_pos.y)

    ##################################################
    # Commands
    ##################################################
    def move(self, tank_id, distance):
        wrapper = self._tanks[tank_id]
        meta = wrapper.meta
        tank = wrapper.entity
        old_pos = Point2(tank.position.x, tank.position.y)
        direction = Vector2(tank.direction.x, tank.direction.y)
        new_pos = old_pos + (direction * distance)
        meta.target_ray = Ray2(new_pos, direction)
        meta.speed = TANK_SPEED


if __name__ == "__main__":
    pass
