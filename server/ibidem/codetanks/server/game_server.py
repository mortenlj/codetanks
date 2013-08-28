#!/usr/bin/env python
# -*- coding: utf-8
from random import randint
import pygame
from pygame.sprite import Sprite
from ibidem.codetanks.server.entities import Tank


class GameServer(object):
    def __init__(self):
        pygame.init()
        self.tanks = pygame.sprite.RenderUpdates()
        self.bullets = pygame.sprite.RenderUpdates()
        self.bounds = pygame.Rect(0, 0, 500, 500)
        self.clock = None
        self._add_random_tank()

    def _add_random_tank(self):
        position = (randint(32, self.bounds.width - 32), randint(32, self.bounds.height - 32))
        direction = (randint(-5, 5), randint(-5, 5))
        while direction == (0, 0):
            direction = (randint(-5, 5), randint(-5, 5))
        self.tanks.add(Tank(position, direction, self.bounds))

    def update(self):
        if self.clock is None:
            self.clock = pygame.time.Clock()
        time_passed = self.clock.tick(50)
        if randint(0, 50) == 0:
            self._add_random_tank()
        self.tanks.update(time_passed)

    def build_game_data(self):
        game_data = {}
        game_data["tanks"] = [t.as_dict() for t in self.tanks]
        game_data["bullets"] = [b.as_dict() for b in self.bullets]
        return game_data

    def build_game_info(self):
        return {
            "arena": {
                "width": self.bounds.width,
                "height": self.bounds.height,
            }
        }


if __name__ == "__main__":
    pass
