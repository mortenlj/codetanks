#!/usr/bin/env python
# -*- coding: utf-8
from random import randint, choice
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
        for i in range(10):
            position = (randint(0, self.bounds.width), randint(0, self.bounds.height))
            direction = (choice([-1, 1]), choice([-1, 1]))
            self.tanks.add(Tank(position, direction, self.bounds))

    def update(self):
        if self.clock is None:
            self.clock = pygame.time.Clock()
        time_passed = self.clock.tick(50)
        self.tanks.update(time_passed)

    def build_game_data(self):
        game_data = {}
        game_data["tanks"] = [t.as_dict() for t in self.tanks]
        game_data["bullets"] = [b.as_dict() for b in self.bullets]
        return game_data


if __name__ == "__main__":
    pass
