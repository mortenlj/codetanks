#!/usr/bin/env python
# -*- coding: utf-8

import uuid
import pygame

from ibidem.codetanks.server.vec2d import vec2d


class MovingEntity(pygame.sprite.Sprite):
    speed = 0.1
    size = 0

    def __init__(self, init_pos, init_dir, bounds=None):
        super(MovingEntity, self).__init__()
        self.id = "%r-%r" % (self.__class__.__name__, uuid.uuid4())
        self.set_position(init_pos)
        self.set_direction(init_dir)
        self.bounds = bounds
        self.base_rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect = self.base_rect.copy()
        self.update_location()

    def set_direction(self, init_dir):
        self.direction = vec2d(init_dir).normalized()

    def set_position(self, init_pos):
        self.position = vec2d(init_pos)

    def as_dict(self):
        return {
            "id": self.id,
            "position": {
                "x": self.position.x,
                "y": self.position.y
            },
            "direction": {
                "x": self.direction.x,
                "y": self.direction.y
            },
            "speed": self.speed,
            "bounds": {
                "left": self.bounds.left,
                "top": self.bounds.top,
                "height": self.bounds.height,
                "width": self.bounds.width
            }
        }

    def update(self, time_passed):
        self.update_vector(time_passed)
        displacement = vec2d(
            self.direction.x * self.speed * time_passed,
            self.direction.y * self.speed * time_passed
        )
        self.position += displacement
        self.update_location()

    def update_vector(self, time_passed):
        raise NotImplementedError()

    def update_location(self):
        self.rect = self.base_rect.move(
            self.position.x - self.size / 2,
            self.position.y - self.size / 2
        )

    def on_collision(self, other):
        raise NotImplementedError()

class Bullet(MovingEntity):
    """A bullet that moves forward until it hits something"""
    speed = 0.5
    size = 5

    def update_vector(self, time_passed):
        pass

    def on_collision(self, other):
        self.kill()


class Tank(MovingEntity):
    speed = 0.1
    size = 46

    def __init__(self, init_pos, init_dir, bounds=None):
        super(Tank, self).__init__(init_pos, init_dir, bounds)
        self.set_aim(init_dir)

    def set_aim(self, init_dir):
        self.aim = vec2d(init_dir).normalized()

    def as_dict(self):
        d = super(Tank, self).as_dict()
        d["aim"] = {
            "x": self.aim.x,
            "y": self.aim.y
        }
        return d

    def update_vector(self, time_passed):
        pass

    def on_collision(self, other):
        self.speed = 0.0

    def cmd_move(self, position):
        # TODO: Make movement smooth
        self.set_position(position)
        self.speed = 0.1

    def cmd_turn(self, direction):
        # TODO: Make movement smooth
        self.set_direction(direction)

    def cmd_aim(self, direction):
        # TODO: Make movement smooth
        self.set_aim(direction)

if __name__ == "__main__":
    pass
