#!/usr/bin/env python
# -*- coding: utf-8

"""
Placeholder for actual data provider
"""
import json

from random import choice, randint
from threading import Thread
from Queue import Queue, Empty
import pygame
from entities import Bullet, Tank

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480

bullet_group = pygame.sprite.RenderUpdates()
bullets = {}
tank_group = pygame.sprite.RenderUpdates()
tanks = {}
queue = Queue()


class Server(Thread):
    def __init__(self, queue, bounds):
        super(Server, self).__init__(name="GameServer")
        self.setDaemon(True)
        self.queue = queue
        self.tanks = pygame.sprite.RenderUpdates()
        self.bullets = pygame.sprite.RenderUpdates()
        self.clock = pygame.time.Clock()
        for i in range(1):
            position = (randint(0, SCREEN_WIDTH), randint(0, SCREEN_HEIGHT))
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


def init(bounds):
    server = Server(queue, bounds)
    server.start()


def update_entities(updates, entities, sprite_group, entity_class):
    for update in updates:
        entity_id = update["id"]
        if entities.has_key(entity_id):
            entity = entities[entity_id]
            entity.update_from_dict(update)
        else:
            entity = entity_class(update)
            sprite_group.add(entity)
            entities[entity.id] = entity


def update_game_data(game_data):
    update_entities(game_data["tanks"], tanks, tank_group, Tank)
    update_entities(game_data["bullets"], bullets, bullet_group, Bullet)


def get(time_passed):
    try:
        game_data = queue.get_nowait()
        update_game_data(json.loads(game_data))
    except Empty:
        bullet_group.update(time_passed)
        tank_group.update(time_passed)
    return bullet_group, tank_group

if __name__ == "__main__":
    pass
