#!/usr/bin/env python
# -*- coding: utf-8

from random import randint
import pygame
from pygame.color import THECOLORS
from pygame.sprite import Sprite
import pymunk
import pymunk.pygame_util
from ibidem.codetanks.server import events
from ibidem.codetanks.server.bodies import Tank


class GameServer(object):
    def __init__(self, debug):
        pygame.init()
        if debug:
            self.screen = pygame.display.set_mode((500, 500))
        else:
            self.screen = None
        self.space = pymunk.Space()
        self.entities = pygame.sprite.Group()
        self.tanks = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.bounds = pygame.Rect(0, 0, 500, 500)
        self.walls = self._init_walls()
        self.clock = None

    def _init_walls(self):
        wallbody = pymunk.Body()
        walls = []
        walls.append(pymunk.Segment(wallbody, self.bounds.topleft, self.bounds.topright, 1))
        walls.append(pymunk.Segment(wallbody, self.bounds.topright, self.bounds.bottomright, 1))
        walls.append(pymunk.Segment(wallbody, self.bounds.bottomright, self.bounds.bottomleft, 1))
        walls.append(pymunk.Segment(wallbody, self.bounds.bottomleft, self.bounds.topleft, 1))
        self.space.add(*walls)
        return walls

    def _create_random_position(self):
        position = (randint(32, self.bounds.width - 32), randint(32, self.bounds.height - 32))
        return position

    def _create_random_direction(self):
        direction = (randint(-5, 5), randint(-5, 5))
        while direction == (0, 0):
            direction = (randint(-5, 5), randint(-5, 5))
        return pymunk.Vec2d(direction)

    def _add_random_tank(self):
        position = self._create_random_position()
        direction = self._create_random_direction()
        tank = Tank(position, direction)
        self.tanks.add(tank)
        self.entities.add(tank)
        self.space.add(tank.body, tank.shape)
        if len(self.tanks) >= 4:
            events.put(events.START_GAME)

    def _apply_dummy_actions(self):
        for t in self.tanks:
            rnd = randint(0, 120)
            if rnd == 0:
                t.cmd_move(self.space, 100)
            if rnd == 1:
                t.cmd_turn(self._create_random_direction())
            if rnd == 2:
                t.cmd_aim(self._create_random_direction())
            if rnd == 3:
                bullet = t.cmd_shoot()
                self.bullets.add(bullet)
                self.entities.add(bullet)

    def start(self):
        self.clock = pygame.time.Clock()

    def started(self):
        return self.clock is not None

    def update(self):
        if self.clock:
            time_passed = self.clock.tick(50)
            dt = 1.0 / 50.0
            self.space.step(dt)
            self._apply_dummy_actions()
            self.entities.update(time_passed)
            if self.screen:
                self.screen.fill(THECOLORS["black"])
                pymunk.pygame_util.draw(self.screen, self.space)
                pygame.display.flip()

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
