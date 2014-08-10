#!/usr/bin/env python
# -*- coding: utf-8

from random import randint

from ibidem.codetanks.domain.constants import TANK_RADIUS
from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point, Bullet
from ibidem.codetanks.server.vehicle import Armour, Missile


class World(object):
    arena = Arena()

    def __init__(self, world_width, world_height):
        self.arena = Arena(world_width, world_height)
        self._bullets = []
        self._tanks = []

    def add_tank(self, bot):
        tank = Armour(Tank(
            bot.tank_id,
            bot.bot_id,
            self._select_valid_position(),
            self._select_random_direction(),
            self._select_random_direction()
        ), self)
        self._tanks.append(tank)

    def add_bullet(self, parent):
        position = Point(parent.position.x, parent.position.y)
        direction = Point(parent.direction.x, parent.direction.y)
        bullet = Missile(Bullet(_bullet_generator.next(), position, direction), self, parent)
        self._bullets.append(bullet)

    @property
    def gamedata(self):
        return GameData(self.bullets, self.tanks)

    @property
    def tanks(self):
        return [w.entity for w in self._tanks]

    @property
    def bullets(self):
        return [w.entity for w in self._bullets]

    def is_valid_position(self, position, current_tank):
        for attr, upper_bound in ((position.x, self.arena.width), (position.y, self.arena.height)):
            if not TANK_RADIUS <= attr <= (upper_bound-TANK_RADIUS):
                return False
        for tank in self._tanks:
            if tank == current_tank: continue
            if tank.collide(position):
                return False
        return True

    def _select_valid_position(self):
        position = Point(randint(0, self.arena.width), randint(0, self.arena.height))
        while not self.is_valid_position(position, None):
            position = Point(randint(0, self.arena.width), randint(0, self.arena.height))
        return position

    def _select_random_direction(self):
        return Point(randint(-1, 1), randint(-1, 1))

    def update(self, ticks):
        for tank in self._tanks:
            tank.update(ticks)
        for bullet in self._bullets:
            bullet.update(ticks)

    def tank_status(self, tank_id):
        return self._tanks[tank_id].status

    def command(self, tank_id, name, *params):
        wrapper = self._tanks[tank_id]
        func = getattr(wrapper, name)
        func(*params)


def _id_generator():
    i = 0
    while True:
        yield i
        i += 1

_bullet_generator = _id_generator()

if __name__ == "__main__":
    pass
