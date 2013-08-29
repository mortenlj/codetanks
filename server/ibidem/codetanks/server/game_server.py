#!/usr/bin/env python
# -*- coding: utf-8
from random import randint
import pygame
from pygame.sprite import Sprite
from ibidem.codetanks.server.entities import Tank


class GameServer(object):
    def __init__(self):
        pygame.init()
        self.entities = pygame.sprite.Group()
        self.tanks = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.bounds = pygame.Rect(0, 0, 500, 500)
        self.clock = None
        for i in range(4):
            self._add_random_tank()

    def _add_random_tank(self):
        position = (randint(32, self.bounds.width - 32), randint(32, self.bounds.height - 32))
        direction = (randint(-5, 5), randint(-5, 5))
        while direction == (0, 0):
            direction = (randint(-5, 5), randint(-5, 5))
        tank = Tank(position, direction, self.bounds)
        self.tanks.add(tank)
        self.entities.add(tank)

    def update(self):
        if self.clock is None:
            self.clock = pygame.time.Clock()
        time_passed = self.clock.tick(50)
        self.entities.update(time_passed)
        self._check_collisions()

    def _check_collisions(self):
        tmp = list(self.entities)
        tmp_rects = [x.rect for x in tmp]
        while tmp:
            entity = tmp.pop()
            entity_rect = tmp_rects.pop()
            idx = entity_rect.collidelistall(tmp_rects)
            for i in idx:
                other = tmp[i]
                entity.on_collision(other)
                other.on_collision(entity)
            if not self.bounds.contains(entity_rect):
                entity.on_collision(None)
                entity_rect.clamp_ip(self.bounds)

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
