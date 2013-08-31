#!/usr/bin/env python
# -*- coding: utf-8

import pkg_resources
import pygame

from ibidem.codetanks.viewer.vec2d import vec2d



class MovingEntity(pygame.sprite.Sprite):
    """A moving entity.
    """
    speed = 0.1

    def __init__(self, init_dict):
        super(MovingEntity, self).__init__()
        self.id = init_dict["id"]
        self.update_from_dict(init_dict)

    def update_from_dict(self, data_dict):
        self.position = vec2d(data_dict["position"]["x"], data_dict["position"]["y"])
        self.direction = vec2d(data_dict["direction"]["x"], data_dict["direction"]["y"])
        self.speed = data_dict["speed"]
        self.update_visuals()

    def update_visuals(self):
        raise NotImplementedError()


class Bullet(MovingEntity):
    """A bullet that moves forward until it hits something"""
    image_name = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", 'bullet_grey.png')
    speed = 0.2

    def __init__(self, init_dict):
        self.base_image = pygame.image.load(self.image_name).convert_alpha()
        super(Bullet, self).__init__(init_dict)

    def update_visuals(self):
        self.image = pygame.transform.rotate(self.base_image, -self.direction.angle)
        self.image_w, self.image_h = self.image.get_size()
        self.rect = self.image.get_rect().move(
            self.position.x - self.image_w / 2,
            self.position.y - self.image_h / 2
        )


class Tank(MovingEntity):
    body_image_name = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "tank1_base_grey.png")
    turret_image_names = (
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "red_turret.png"),
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "blue_turret.png"),
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "green_turret.png"),
        pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", "yellow_turret.png")
    )
    speed = 0.1

    def __init__(self, init_dict):
        self.player_number = init_dict["player_number"]
        self.base_body_image = pygame.image.load(self.body_image_name).convert_alpha()
        self.base_turret_image = pygame.image.load(self.turret_image_names[self.player_number]).convert_alpha()
        super(Tank, self).__init__(init_dict)

    def update_from_dict(self, data_dict):
        self.aim = vec2d(data_dict["aim"]["x"], data_dict["aim"]["y"])
        self.health = data_dict["health"]
        super(Tank, self).update_from_dict(data_dict)

    def update_visuals(self):
        self.image = pygame.transform.rotate(self.base_body_image, -self.direction.angle)
        self.image_w, self.image_h = self.image.get_size()
        new_turret_image = pygame.transform.rotate(self.base_turret_image, -self.aim.angle)
        w, h = new_turret_image.get_size()
        rect = new_turret_image.get_rect().move((self.image_w / 2) - (w / 2), (self.image_h / 2) - (h / 2))
        self.image.blit(new_turret_image, rect)
        self.rect = self.image.get_rect().move(
            self.position.x - self.image_w / 2,
            self.position.y - self.image_h / 2
        )


if __name__ == "__main__":
    pass
