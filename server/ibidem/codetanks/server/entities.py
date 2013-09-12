#!/usr/bin/env python
# -*- coding: utf-8

__all__ = ["Tank", "Bullet"]

from Queue import Queue, Empty

import pygame
from ibidem.codetanks.server.commands import Move, Command, Turn, Aim

from ibidem.codetanks.server.vec2d import vec2d


def id_generator():
    i = 0
    while True:
        yield i
        i += 1

id_series = id_generator()
player_series = id_generator()


class EntityEncoder(object):
    def to_serializable(self, o):
        name = "_encode_" + o.__class__.__name__.lower()
        m = getattr(self, name, self._identity)
        return m(o)

    def _identity(self, o):
        return o

    def _encode_tank(self, tank):
        d = self._encode_common_moving(tank)
        d["player_number"] = tank.player_number
        d["aim"] = self.to_serializable(tank.aim)
        d["health"] = tank.health
        return d

    def _encode_bullet(self, bullet):
        return self._encode_common_moving(bullet)

    def _encode_common_moving(self, moving):
        return {
            "id": moving.id,
            "position": self.to_serializable(moving.position),
            "direction": self.to_serializable(moving.direction),
        }

    def _encode_vec2d(self, vector):
        return {
            "x": vector.x,
            "y": vector.y
        }


class MovingEntity(pygame.sprite.Sprite):
    speed = 0.1
    size = 0

    def __init__(self, init_pos, init_dir):
        super(MovingEntity, self).__init__()
        self.id = "%s-%s" % (self.__class__.__name__, id_series.next())
        self.set_direction(init_dir)
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.position = init_pos
        self.update_location(0)

    def set_direction(self, init_dir):
        self.direction = vec2d(init_dir).normalized()

    @property
    def position(self):
        return vec2d(self.rect.center)

    @position.setter
    def position(self, vec_or_pair):
        if isinstance(vec_or_pair, vec2d):
            vec_or_pair = (vec_or_pair.x, vec_or_pair.y)
        self.rect.center = vec_or_pair

    def as_dict(self):
        pass

    def update(self, time_passed):
        self.update_vector(time_passed)
        self.update_location(time_passed)

    def clamp(self, bounds):
        self.rect.clamp_ip(bounds)

    def update_vector(self, time_passed):
        pass

    def update_location(self, time_passed):
        pass

    def on_collision(self, other):
        raise NotImplementedError()

    def __str__(self):
        return self.id


class Bullet(MovingEntity):
    """A bullet that moves forward until it hits something"""
    speed = 0.3
    size = 5
    imparted_damage = 5

    def __init__(self, init_pos, init_dir, parent):
        super(Bullet, self).__init__(init_pos, init_dir)
        self.parent = parent

    def as_dict(self):
        return EntityEncoder().to_serializable(self)

    def update_location(self, time_passed):
        displacement = vec2d(
            self.direction.x * self.speed * time_passed,
            self.direction.y * self.speed * time_passed
        )
        self.position += displacement

    def on_collision(self, other):
        if not isinstance(other, Bullet) and not other == self.parent:
            self.kill()

    def __str__(self):
        return super(Bullet, self).__str__() + ", fired by %s" % self.parent


class Tank(MovingEntity):
    health = 100
    imparted_damage = 0
    speed = 0.1
    turn_rate = 0.1
    turret_rate = 0.2
    size = 46

    def __init__(self, init_pos, init_dir):
        super(Tank, self).__init__(init_pos, init_dir)
        self.player_number = player_series.next()
        self.aim = vec2d(init_dir).normalized()
        self.speed = 0.0
        self.bullets = pygame.sprite.Group()
        self.cmd_queue = Queue()
        self.cmd = Command(self)

    def as_dict(self):
        return EntityEncoder().to_serializable(self)

    def update(self, time_passed):
        self.cmd.update(time_passed)
        super(Tank, self).update(time_passed)
        if self.cmd.finished():
            try:
                self.cmd = self.cmd_queue.get_nowait()
            except Empty:
                if not isinstance(self.cmd, Command):
                    self.cmd = Command(self)
        if self.health <= 0:
            self.kill()

    def on_collision(self, other):
        if other in self.bullets:
            return
        if other:
            self.health -= other.imparted_damage
        if not isinstance(other, Bullet):
            self.cmd.abort()

    def cmd_move(self, distance, tanks, walls):
        self.cmd_queue.put(Move(self, distance, tanks, walls))

    def cmd_turn(self, direction):
        self.cmd_queue.put(Turn(self, direction))

    def cmd_aim(self, direction):
        self.cmd_queue.put(Aim(self, direction))

    def cmd_shoot(self):
        position = self.position + (self.aim * (self.size / 2))
        bullet = Bullet(position, self.aim, self)
        self.bullets.add(bullet)
        return bullet

if __name__ == "__main__":
    pass
