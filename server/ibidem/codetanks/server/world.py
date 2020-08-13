#!/usr/bin/env python
# -*- coding: utf-8

import logging
import math
from collections import defaultdict
from random import randint

from euclid import LineSegment2, Circle

from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point, Bullet, ScanResult, BotStatus, Event
from ibidem.codetanks.server.constants import MAX_HEALTH
from ibidem.codetanks.server.debug_util import ScanPlot
from ibidem.codetanks.server.vehicle import Armour, Missile

LOG = logging.getLogger(__name__)


class World(object):
    arena = Arena()

    def __init__(self, world_width, world_height, debug):
        LOG.debug("Creating world %dx%d (debug: %r)", world_width, world_height, debug)
        self.arena = Arena(world_width, world_height)
        self._bullets = []
        self._tanks = []
        self._events = defaultdict(list)
        self._debug = debug

    def add_tank(self, bot_id, tank_id):
        armour = Armour(Tank(
            tank_id,
            bot_id,
            None,
            self._select_random_direction(),
            self._select_random_direction(),
            MAX_HEALTH,
            BotStatus.IDLE
        ), self)
        self._set_valid_position(armour)
        self._tanks.append(armour)
        return armour

    def add_bullet(self, parent):
        position = Point(parent.position.x, parent.position.y)
        direction = Point(parent.turret.x, parent.turret.y)
        bullet = Missile(Bullet(next(_bullet_generator), position, direction), self, parent)
        self._bullets.append(bullet)

    def remove_bullet(self, missile):
        self._bullets.remove(missile)

    @property
    def gamedata(self):
        return GameData(self.bullets, self.tanks)

    @property
    def tanks(self):
        return [w.entity for w in self._tanks]

    @property
    def bullets(self):
        return [w.entity for w in self._bullets]

    @property
    def number_of_live_bots(self):
        return len([w for w in self._tanks if w.status != BotStatus.DEAD])

    def is_collision(self, vehicle):
        position = vehicle.position
        for attr, upper_bound in ((position.x, self.arena.width), (position.y, self.arena.height)):
            if not vehicle.radius <= attr <= (upper_bound-vehicle.radius):
                return True
        for tank in self._tanks:
            if vehicle.collide(tank):
                return tank
        return False

    def _set_valid_position(self, armour):
        armour.position = Point(randint(0, self.arena.width), randint(0, self.arena.height))
        while self.is_collision(armour):
            armour.position = Point(randint(0, self.arena.width), randint(0, self.arena.height))

    def _select_random_direction(self):
        x = randint(-1, 1)
        y = randint(-1, 1)
        while x == y == 0:
            y = randint(-1, 1)
        return Point(x, y)

    def update(self, ticks):
        for tank in self._tanks:
            tank.update(ticks)
        for bullet in self._bullets:
            bullet.update(ticks)

    def scan(self, ray, theta):
        radius = self._calculate_scan_radius(theta)
        LOG.debug("Scanning along %r, with spread %.2f, radius is %d", ray, theta, radius)
        hits = []
        for tank in self._tanks:
            if tank.position == ray.p:
                continue
            if self._is_hit(ray, theta, tank):
                hits.append(tank.entity)
        return Event(scan=ScanResult(hits))

    def _calculate_scan_radius(self, theta):
        return max(math.pi - theta, 0.0) * (self.arena.height * 0.318)

    def _is_hit(self, ray, theta, tank):
        radius = self._calculate_scan_radius(theta)
        center_line = LineSegment2(ray.p, ray.v, radius)
        center_vector = ray.v
        target_line = LineSegment2(ray.p, tank.position)
        tank_circle = Circle(tank.position, float(tank.radius))
        bounds = theta/2.
        if theta == 0.:
            left = right = center_line
        else:
            left = LineSegment2(ray.p, center_vector.rotate(bounds), radius)
            right = LineSegment2(ray.p, center_vector.rotate(-bounds), radius)
        LOG.debug("Checking if %r is inside sector between %r and %r with radius %r", tank.position, left, right, radius)
        if self._debug:
            ScanPlot(self.arena.width, self.arena.height, left, right, center_line, radius, tank).plot()
        if target_line.length > radius:
            LOG.debug("Outside because %r is %r from center, which is more than radius %r", tank.position, target_line.length, radius)
            return False
        for side in left, right:
            intersect = side.intersect(tank_circle)
            if intersect:
                LOG.debug("Inside because tank intersects side vector (%r) at %r", side, intersect)
                return True
        if target_line.v.angle(center_line.v) > bounds:
            LOG.debug("Outside because %r is further from the center line than %r", target_line.v,  bounds)
            return False
        LOG.debug("Inside sector")
        return True

    def get_events(self):
        events = self._events
        self._events = defaultdict(list)
        return events

    def add_event(self, tank_id, event):
        self._events[tank_id].append(event)


def _id_generator():
    i = 0
    while True:
        yield i
        i += 1

_bullet_generator = _id_generator()
_debug_generator = _id_generator()

if __name__ == "__main__":
    pass
