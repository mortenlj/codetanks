#!/usr/bin/env python
# -*- coding: utf-8

from ibidem.codetanks.domain.ttypes import GameData, Arena


class World(GameData):
    arena = Arena(0, 0)

    def __init__(self, world_width, world_height):
        super(World, self).__init__([], [])
        self.arena = Arena(world_width, world_height)

    def add_tank(self, bot):
        pass

if __name__ == "__main__":
    pass
