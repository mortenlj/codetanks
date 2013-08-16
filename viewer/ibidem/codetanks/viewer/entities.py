#!/usr/bin/env python
# -*- coding: utf-8

import pkg_resources
import pygame

from ibidem.codetanks.viewer.vec2d import vec2d


class MovingEntity(pygame.sprite.Sprite):
    """A moving entity.

    Subclass must implement update_location and update_visauls
    It can optionally change the attributes speed and image_name
    """
    speed = 0.1
    image_name = ""

    def __init__(self, init_pos, init_dir, bounds):
        super(MovingEntity, self).__init__()
        self.position = vec2d(init_pos)
        self.direction = vec2d(init_dir).normalized()
        self.base_image = pygame.image.load(self.image_name).convert_alpha()
        self.bounds = bounds
        self.update_visuals()

    def update(self, time_passed):
        self.update_vector(time_passed)
        displacement = vec2d(
            self.direction.x * self.speed * time_passed,
            self.direction.y * self.speed * time_passed
        )
        self.position += displacement
        self.update_visuals()
        if not self.bounds.contains(self.rect):
            self.on_wall_collision()

    def update_vector(self, time_passed):
        raise NotImplementedError()

    def update_visuals(self):
        raise NotImplementedError()

    def on_wall_collision(self):
        raise NotImplementedError()


class Bullet(MovingEntity):
    """A bullet that moves forward until it hits something"""
    image_name = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", 'bullet_grey.png')
    speed = 0.2

    def update_vector(self, time_passed):
        pass

    def update_visuals(self):
        self.image = pygame.transform.rotate(self.base_image, -self.direction.angle)
        self.image_w, self.image_h = self.image.get_size()
        self.rect = self.image.get_rect().move(
            self.position.x - self.image_w / 2,
            self.position.y - self.image_h / 2
        )

    def on_wall_collision(self):
        self.kill()


class Tank(MovingEntity):
    image_name = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "mockup_tank1.png")
    speed = 0.1

    def update_vector(self, time_passed):
        if self.speed == 0.0:
            self.direction.rotate(10)
            self.speed = 0.1

    def update_visuals(self):
        self.image = pygame.transform.rotate(self.base_image, -self.direction.angle)
        self.image_w, self.image_h = self.image.get_size()
        self.rect = self.image.get_rect().move(
            self.position.x - self.image_w / 2,
            self.position.y - self.image_h / 2
        )

    def on_wall_collision(self):
        self.speed = 0.0


if __name__ == "__main__":
    pass
