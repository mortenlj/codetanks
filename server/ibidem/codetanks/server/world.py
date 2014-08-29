#!/usr/bin/env python
# -*- coding: utf-8

from random import randint
import math
import logging

from euclid import Circle, LineSegment2

from ibidem.codetanks.domain.ttypes import GameData, Arena, Tank, Point, Bullet, ScanResult
from ibidem.codetanks.server.vehicle import Armour, Missile


LOG = logging.getLogger(__name__)


class World(object):
    arena = Arena()

    def __init__(self, world_width, world_height):
        self.arena = Arena(world_width, world_height)
        self._bullets = []
        self._tanks = []
        self._events = {}

    def add_tank(self, bot):
        armour = Armour(Tank(
            bot.tank_id,
            bot.bot_id,
            None,
            self._select_random_direction(),
            self._select_random_direction()
        ), self)
        self._set_valid_position(armour)
        self._tanks.append(armour)

    def add_bullet(self, parent):
        position = Point(parent.position.x, parent.position.y)
        direction = Point(parent.turret.x, parent.turret.y)
        bullet = Missile(Bullet(_bullet_generator.next(), position, direction), self, parent)
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

    def tank_status(self, tank_id):
        return self._tanks[tank_id].status

    def scan(self, ray, theta):
        radius = self._calculate_scan_radius(theta)
        LOG.debug("Scanning along %r, with spread %.2f, radius is %d", ray, theta, radius)
        if theta == 0.00:
            line = LineSegment2(ray.p, ray.v, radius)
            check_func = lambda tank: self._is_in_scanline(line, tank)
        else:
            center_vector = ray.v
            left = LineSegment2(ray.p, center_vector.rotate(theta/2.), radius)
            right = LineSegment2(ray.p, center_vector.rotate(-theta/2.), radius)
            LOG.debug("Left: %r, Right: %r", left, right)
            check_func = lambda tank: self._is_inside_sector(left, right, radius, tank.position)
        hits = []
        for tank in self._tanks:
            if tank.position == ray.p:
                continue
            if check_func(tank):
                hits.append(tank.entity)
        return ScanResult(hits)

    def _calculate_scan_radius(self, theta):
        return max(math.pi - theta, 0.0) * (self.arena.height * 0.318)

    def _is_in_scanline(self, line, tank):
        ##### DEBUG PLOT
        from cairocffi import SVGSurface, Context
        debug_plot_id = _debug_generator.next()
        s = SVGSurface("debug_plot%05d.svg" % debug_plot_id, self.arena.width, self.arena.height)
        c = Context(s)
        c.set_source_rgb(0.0, 0.0, 0.0)
        c.paint()
        c.move_to(line.p1.x, line.p1.y)
        c.line_to(line.p2.x, line.p2.y)
        c.set_source_rgb(1., 0., 0.)
        c.stroke()
        c.new_sub_path()
        c.arc(tank.position.x, tank.position.y, tank.radius, 0, math.pi*2)
        c.set_source_rgb(1.0, 1.0, 0)
        c.stroke_preserve()
        c.set_source_rgb(1.0, 0., 1.0)
        c.fill()
        s.finish()
        return line.intersect(Circle(tank.position, float(tank.radius)))

    def _is_inside_sector(self, left, right, radius, position):
        ##### DEBUG PLOT
        from cairocffi import SVGSurface, Context
        debug_plot_id = _debug_generator.next()
        s = SVGSurface("debug_plot%05d.svg" % debug_plot_id, self.arena.width, self.arena.height)
        c = Context(s)
        c.set_source_rgb(0.0, 0.0, 0.0)
        c.paint()
        c.move_to(left.p1.x, left.p1.y)
        c.line_to(left.p2.x, left.p2.y)
        c.move_to(right.p1.x, right.p1.y)
        c.line_to(right.p2.x, right.p2.y)
        c.set_source_rgb(1., 0., 0.)
        c.stroke()
        c.new_sub_path()
        c.arc(position.x, position.y, 1, 0, math.pi*2)
        c.new_sub_path()
        c.arc(position.x, position.y, 16, 0, math.pi*2)
        c.set_source_rgb(1.0, 0., 1.0)
        c.fill_preserve()
        c.set_source_rgb(1.0, 1.0, 0)
        c.stroke()
        c.new_sub_path()
        c.arc(left.p1.x, left.p1.y, radius, 0, math.pi*2)
        c.set_source_rgb(0., 1., 0.)
        c.stroke()
        s.finish()
        scan_line = LineSegment2(left.p1, position)
        LOG.debug("Checking if %r is inside sector between %r and %r with radius %r", position, left, right, radius)
        LOG.debug("Using %r to perform check", scan_line)
        if scan_line.length > radius:
            LOG.debug("Outside because %r is %r from center, which is more than radius %r", position, scan_line.length, radius)
            return False
        if not left.v.clockwise(scan_line.v):
            LOG.debug("Outside because %r is not clockwise of left vector (%r)", scan_line.v, left)
            return False
        if right.v.clockwise(scan_line.v):
            LOG.debug("Outside because %r is clockwise of right vector (%r)", scan_line.v, right)
            return False
        return True

    def command(self, tank_id, name, *params):
        wrapper = self._tanks[tank_id]
        func = getattr(wrapper, name)
        func(*params)

    def get_events(self):
        events = self._events
        self._events = {}
        return events

    def add_event(self, tank_id, event):
        if not self._events.has_key(tank_id):
            self._events[tank_id] = []
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
