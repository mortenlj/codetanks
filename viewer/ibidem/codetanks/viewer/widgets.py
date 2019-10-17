#!/usr/bin/env python
# -*- coding: utf-8

import pkg_resources
import pygame


class Arena(object):
    ground = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", 'bg_grass.png')
    wall = pkg_resources.resource_filename("ibidem.codetanks.viewer.resources", 'bg_wall2.png')

    def __init__(self, width, height):
        self.wall_image = pygame.image.load(self.wall).convert_alpha()
        self.ground_image = pygame.image.load(self.ground).convert_alpha()
        self.sprite_size = self.ground_image.get_width()
        self.surface = pygame.Surface((width + (2*self.sprite_size), height + (2* self.sprite_size)))
        self.game_field = self.surface.subsurface((self.sprite_size, self.sprite_size, width, height))
        for x in range(0, self.get_width(), self.sprite_size):
            for y in range(0, self.get_height(), self.sprite_size):
                image = self.ground_image
                if y == 0 or x == 0:
                    image = self.wall_image
                self.surface.blit(image, (x, y))
        for x in range(0, self.get_width(), self.sprite_size):
            self.surface.blit(self.wall_image, (x, self.get_height()- self.sprite_size))
        for y in range(0, self.get_height(), self.sprite_size):
            self.surface.blit(self.wall_image, (self.get_width()- self.sprite_size, y))
        self.background = self.game_field.copy()

    def draw(self, target, dest):
        target.blit(self.surface, dest)

    def get_width(self):
        return self.surface.get_width()

    def get_height(self):
        return self.surface.get_height()


class TankInfo(object):
    foreground_color = (255, 255, 255)
    background_color = (32, 32, 32)
    health_start = (255, 0, 0)
    health_end = (0, 255, 0)

    def __init__(self, tank):
        self.tank = tank
        self.surface = pygame.Surface((256, 64))
        self.font = pygame.font.Font(None, 16)
        name = "%s [%d]" % (self.tank.bot_id.name, self.tank.id)
        self.name = self.font.render(name, True, self.foreground_color, self.background_color)

    def draw(self, target, dest):
        self.surface.fill(self.background_color)
        self._draw_health_bar()
        self._draw_health_number()
        self._draw_tank()
        self._draw_name()
        target.blit(self.surface, dest)

    def _draw_health_bar(self):
        health_bar = self.surface.subsurface((64, 24, 64, 16))
        end_x = int((health_bar.get_width() / 100.0) * self.tank.health)
        self._draw_gradient(health_bar, end_x)

    def _draw_health_number(self):
        health = self.font.render(unicode(self.tank.health), True, self.foreground_color, self.background_color)
        self.surface.blit(health, (136, 32))

    def _draw_tank(self):
        top = 28 - (self.tank.image.get_height()/2)
        left = 28 - (self.tank.image.get_width()/2)
        self.surface.blit(self.tank.image, (top, left))

    def _draw_name(self):
        self.surface.blit(self.name, (136, 8))

    def _draw_gradient(self, surface, end_x):
        rect = surface.get_rect()
        x1, x2 = rect.left, rect.right
        y1, y2 = rect.top, rect.bottom
        h = x2 - x1
        a = self.health_start
        b = self.health_end
        rate = (
            float(b[0] - a[0]) / h,
            float(b[1] - a[1]) / h,
            float(b[2] - a[2]) / h
        )
        fn_line = pygame.draw.line
        for col in range(x1, end_x):
            color = (
                min(max(a[0] + (rate[0] * (col - x1)), 0), 255),
                min(max(a[1] + (rate[1] * (col - x1)), 0), 255),
                min(max(a[2] + (rate[2] * (col - x1)), 0), 255)
            )
            fn_line(surface, color, (col, y1), (col, y2))


if __name__ == "__main__":
    pass
