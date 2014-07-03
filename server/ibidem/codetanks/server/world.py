#!/usr/bin/env python
# -*- coding: utf-8

from ibidem.codetanks.domain.ttypes import GameData, Arena


class World(object):
    arena = Arena(0, 0)

    def __init__(self, world_width, world_height):
        self.arena = Arena(world_width, world_height)

    def add_tank(self, bot):
        pass

    def build_game_data(self):
        return GameData([], [])

if __name__ == "__main__":
    pass
