#!/usr/bin/env python
# -*- coding: utf-8

from random import randint, uniform

from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point


class _Meta(object):
    __slots__ = [
        'target_position'
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


if __name__ == "__main__":
    pass
