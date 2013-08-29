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

    def _create_random_position(self):
        position = (randint(32, self.bounds.width - 32), randint(32, self.bounds.height - 32))
        return position

    def _create_random_direction(self):
        direction = (randint(-5, 5), randint(-5, 5))
        while direction == (0, 0):
            direction = (randint(-5, 5), randint(-5, 5))
        return direction

    def _add_random_tank(self):
        position = self._create_random_position()
        direction = self._create_random_direction()
        tank = Tank(position, direction, self.bounds)
        self.tanks.add(tank)
        self.entities.add(tank)

    def _apply_dummy_actions(self):
        for t in self.tanks:
            rnd = randint(0, 120)
            if rnd == 0:
                t.cmd_move(randint(10, 100))
            if rnd == 1:
                t.cmd_turn(self._create_random_direction())
            if rnd == 2:
                t.cmd_aim(self._create_random_direction())

    def update(self):
        if self.clock is None:
            self.clock = pygame.time.Clock()
        time_passed = self.clock.tick(50)
        self._apply_dummy_actions()
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
                entity.clamp(self.bounds)

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
