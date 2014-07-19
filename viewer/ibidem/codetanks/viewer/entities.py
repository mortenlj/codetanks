#!/usr/bin/env python
# -*- coding: utf-8

import pkg_resources
import pygame

from ibidem.codetanks.viewer.vec2d import vec2d


class Entity(pygame.sprite.Sprite):
    """An entity.
    """

    def __init__(self, e):
        super(Entity, self).__init__()
        self.id = e.id
        self.position = vec2d(e.position.x, e.position.y)
        self.direction = vec2d(e.direction.x, e.direction.y)

    def update_visuals(self):
        raise NotImplementedError()


class Bullet(Entity):
    """A bullet that moves forward until it hits something"""
    image_name = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", 'bullet_grey.png')

    def __init__(self, e):
        super(Bullet, self).__init__(e)
        self.base_image = pygame.image.load(self.image_name).convert_alpha()

    def update_visuals(self):
        self.image = pygame.transform.rotate(self.base_image, -self.direction.angle)
        self.image_w, self.image_h = self.image.get_size()
        self.rect = self.image.get_rect().move(
            self.position.x - self.image_w / 2,
            self.position.y - self.image_h / 2
        )


class Tank(Entity):
    body_image_name = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "tank1_base_grey.png")
    turret_image_names = (
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "red_turret.png"),
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "blue_turret.png"),
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "green_turret.png"),
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "yellow_turret.png")
    )

    def __init__(self, e):
        super(Tank, self).__init__(e)
        self.bot_id = e.bot_id
        self.turret = vec2d(e.turret.x, e.turret.y)
        self.health = e.health
        self.base_body_image = pygame.image.load(self.body_image_name).convert_alpha()
        self.base_turret_image = pygame.image.load(self.turret_image_names[self.id % len(self.turret_image_names)]).convert_alpha()

    def update_visuals(self):
        self.image = pygame.transform.rotate(self.base_body_image, -self.direction.angle)
        self.image_w, self.image_h = self.image.get_size()
        new_turret_image = pygame.transform.rotate(self.base_turret_image, -self.turret.angle)
        w, h = new_turret_image.get_size()
        rect = new_turret_image.get_rect().move((self.image_w / 2) - (w / 2), (self.image_h / 2) - (h / 2))
        self.image.blit(new_turret_image, rect)
        self.rect = self.image.get_rect().move(
            self.position.x - self.image_w / 2,
            self.position.y - self.image_h / 2
        )


if __name__ == "__main__":
    pass
