#!/usr/bin/env python
# -*- coding: utf-8

import pygame

from ibidem.codetanks.server.vec2d import vec2d

def id_generator():
    i = 0
    while True:
        yield i
        i += 1

id_series = id_generator()
player_series = id_generator()

class MovingEntity(pygame.sprite.Sprite):
    speed = 0.1
    size = 0

    def __init__(self, init_pos, init_dir):
        super(MovingEntity, self).__init__()
        self.id = "%s-%s" % (self.__class__.__name__, id_series.next())
        self.set_position(init_pos)
        self.set_direction(init_dir)
        self.base_rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect = self.base_rect.copy()
        self.update_location(0)

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
        }

    def update(self, time_passed):
        self.update_vector(time_passed)
        self.update_location(time_passed)

    def clamp(self, bounds):
        self.rect.clamp_ip(bounds)
        self.position = vec2d(self.rect.center)

    def update_vector(self, time_passed):
        pass

    def update_location(self, time_passed):
        displacement = vec2d(
            self.direction.x * self.speed * time_passed,
            self.direction.y * self.speed * time_passed
        )
        self.position += displacement
        self.rect = self.base_rect.move(
            self.position.x - self.size / 2,
            self.position.y - self.size / 2
        )

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
        self.target_direction = self.direction
        self.target_aim = self.aim
        self.target_rect = pygame.Rect(self.position.x - 1, self.position.y - 1, 2, 2)
        self.bullets = pygame.sprite.Group()

    def as_dict(self):
        d = super(Tank, self).as_dict()
        d["player_number"] = self.player_number
        d["aim"] = {
            "x": self.aim.x,
            "y": self.aim.y
        }
        d["health"] = self.health
        return d

    def _calculate_angle_adjustment(self, time_passed, current, target, rate):
        adjustment = 0
        angle = current.get_angle_between(target)
        if angle:
            adjustment = rate * time_passed
            if abs(angle) < adjustment:
                adjustment = angle
            elif angle < 0:
                adjustment = -adjustment
        return adjustment

    def update(self, time_passed):
        super(Tank, self).update(time_passed)
        if hasattr(self, "target_rect") and self.target_rect.colliderect(self.rect):
            self.speed = 0.0
        if self.health <= 0:
            self.kill()

    def update_vector(self, time_passed):
        adjustment = self._calculate_angle_adjustment(time_passed, self.direction, self.target_direction, Tank.turn_rate)
        self.direction.rotate(adjustment)
        adjustment = self._calculate_angle_adjustment(time_passed, self.aim, self.target_aim, Tank.turret_rate)
        self.aim.rotate(adjustment)

    def on_collision(self, other):
        if other in self.bullets:
            return
        if other:
            self.health -= other.imparted_damage
        if not isinstance(other, Bullet):
            self.speed = 0.0

    def cmd_move(self, distance):
        target_position = self.position + (self.direction * distance)
        self.target_rect = pygame.Rect(target_position.x - 1, target_position.y - 1, 2, 2)
        self.speed = Tank.speed

    def cmd_turn(self, direction):
        self.target_direction = direction

    def cmd_aim(self, direction):
        self.target_aim = direction

    def cmd_shoot(self):
        position = self.position + (self.aim * (self.size / 2))
        bullet = Bullet(position, self.aim, self)
        self.bullets.add(bullet)
        return bullet

if __name__ == "__main__":
    pass
