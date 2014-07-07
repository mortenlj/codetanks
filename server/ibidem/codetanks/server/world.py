#!/usr/bin/env python
# -*- coding: utf-8

from random import randint, uniform

from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point


class World(object):
    arena = Arena()
    gamedata = GameData()

    def __init__(self, world_width, world_height):
        self.arena = Arena(world_width, world_height)
        self.gamedata = GameData([], [])

    def add_tank(self, bot):
        tank = Tank(
            bot.tank_id,
            bot.bot_id,
            self._select_valid_position(),
            self._select_random_direction(),
            self._select_random_direction()
        )
        self.tanks.append(tank)

    @property
    def tanks(self):
        return self.gamedata.tanks

    @property
    def bullets(self):
        return self.gamedata.bullets

    def _select_valid_position(self):
        return Point(randint(0, self.arena.width), randint(0, self.arena.height))

    def _select_random_direction(self):
        return Point(uniform(-1, 1), uniform(-1, 1))


if __name__ == "__main__":
    pass
