#!/usr/bin/env python
# -*- coding: utf-8

"""
Placeholder for actual data provider
"""
import json

from random import choice, randint
from threading import Thread
import pygame
from entities import Bullet, Tank


class Server(Thread):
    def __init__(self, queue, bounds):
        super(Server, self).__init__(name="GameServer")
        self.setDaemon(True)
        self.queue = queue
        self.tanks = pygame.sprite.RenderUpdates()
        self.bullets = pygame.sprite.RenderUpdates()
        self.clock = pygame.time.Clock()
        for i in range(1):
            position = (randint(0, bounds.width), randint(0, bounds.height))
            direction = (choice([-1, 1]), choice([-1, 1]))
            self.tanks.add(Tank(position, direction, bounds))

    def run(self):
        while True:
            time_passed = self.clock.tick(50)
            self.tanks.update(time_passed)
            self.bullets.update(time_passed)
            game_data = self.build_game_data()
            self.queue.put(json.dumps(game_data))
            pygame.time.delay(randint(0, 300))

    def build_game_data(self):
        game_data = {}
        game_data["tanks"] = [t.as_dict() for t in self.tanks]
        game_data["bullets"] = [b.as_dict() for b in self.bullets]
        return game_data

if __name__ == "__main__":
    pass
