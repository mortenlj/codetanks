#!/usr/bin/env python
# -*- coding: utf-8
from Queue import Queue, Empty

import pygame
import pymunk
from ibidem.codetanks.server.commands import Command, Move, Turn, Aim
from ibidem.codetanks.server.entities import EntityEncoder, Bullet


def id_generator():
    i = 0
    while True:
        yield i
        i += 1


id_series = id_generator()
player_series = id_generator()


class Tank(pygame.sprite.Sprite):
    health = 100
    mass = 10
    size = 16
    moment = pymunk.moment_for_circle(mass, 0, size)

    def __init__(self, position, direction):
        super(Tank, self).__init__()
        self.id = "%s-%s" % (self.__class__.__name__, id_series.next())
        self.body = pymunk.Body(self.mass, self.moment)
        self.body.position = position
        self.shape = pymunk.Circle(self.body, self.size)
        self.shape.group = player_series.next()
        self.shape.tank = self
        self.direction = direction
        self.aim = self.direction
        self.cmd_queue = Queue()
        self.cmd = Command(self)

    def as_dict(self):
        return EntityEncoder().to_serializable(self)

    def update(self, time_passed):
        self.cmd.update(time_passed)
        if self.cmd.finished():
            try:
                self.cmd = self.cmd_queue.get_nowait()
            except Empty:
                if not isinstance(self.cmd, Command):
                    self.cmd = Command(self)

    def cmd_move(self, space, distance):
        self.cmd_queue.put(Move(space, self, distance))

    def cmd_turn(self, direction):
        self.cmd_queue.put(Turn(self, direction))

    def cmd_aim(self, direction):
        self.cmd_queue.put(Aim(self, direction))

    def cmd_shoot(self):
        # TODO: Replace with pymunk-based bullet
        bullet = Bullet(self.position, self.aim, self)
        return bullet

    def stop(self):
        self.body.reset_forces()
        self.body.velocity = (0, 0)

    @property
    def player_number(self):
        return self.shape.group

    @property
    def direction(self):
        v = pymunk.Vec2d.ones()
        v.angle = self.body.angle
        return v

    @direction.setter
    def direction(self, angle):
        if isinstance(angle, float):
            self.body.angle = angle
        else:
            self.body.angle = angle.angle

    @property
    def position(self):
        return self.body.position

    @property
    def collision_type(self):
        return self.shape.group

    def __str__(self):
        return self.id

if __name__ == "__main__":
    pass
