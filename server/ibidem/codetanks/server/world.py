#!/usr/bin/env python
# -*- coding: utf-8

from random import randint

from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point


class World(GameData):
    arena = Arena(0, 0)

    def __init__(self, world_width, world_height):
        super(World, self).__init__([], [])
        self.arena = Arena(world_width, world_height)

    def add_tank(self, bot):
        self.tanks.append(Tank(bot.tank_id, bot.bot_id, self._select_valid_position()))
        pass

    def _select_valid_position(self):
        return Point(randint(0, self.arena.width), randint(0, self.arena.height))


if __name__ == "__main__":
    pass
