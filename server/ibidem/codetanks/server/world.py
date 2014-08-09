#!/usr/bin/env python
# -*- coding: utf-8

from random import randint

from ibidem.codetanks.domain.constants import TANK_RADIUS
from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point
from ibidem.codetanks.server.vehicle import Vehicle


class World(object):
    arena = Arena()

    def __init__(self, world_width, world_height):
        self.arena = Arena(world_width, world_height)
        self._bullets = []
        self._tanks = []

    def add_tank(self, bot):
        tank = Vehicle(Tank(
            bot.tank_id,
            bot.bot_id,
            self._select_valid_position(),
            self._select_random_direction(),
            self._select_random_direction()
        ), self)
        self._tanks.append(tank)

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
        for tank_wrapper in self._tanks:
            tank_wrapper.update(ticks)

    def tank_status(self, tank_id):
        return self._tanks[tank_id].status

    ##################################################
    # Commands
    ##################################################
    def move(self, tank_id, distance):
        wrapper = self._tanks[tank_id]
        wrapper.move(distance)

    def rotate(self, tank_id, angle):
        wrapper = self._tanks[tank_id]
        wrapper.rotate(angle)

    def aim(self, tank_id, angle):
        wrapper = self._tanks[tank_id]
        wrapper.aim(angle)

    def fire(self, tank_id):
        wrapper = self._tanks[tank_id]
        wrapper.fire()


if __name__ == "__main__":
    pass
