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
        self.surface = pygame.Surface((width + (2*self.wall_image.get_width()), height + (2*self.wall_image.get_height())))
        gwidth = self.ground_image.get_width()
        gheight = self.ground_image.get_height()
        for x in range(0, self.get_width(), gwidth):
            for y in range(0, self.get_height(), gheight):
                image = self.ground_image
                if y == 0 or x == 0:
                    image = self.wall_image
                self.surface.blit(image, (x, y))
        for x in range(0, self.get_width(), gwidth):
            self.surface.blit(self.wall_image, (x, self.get_height()-gheight))
        for y in range(0, self.get_height(), gheight):
            self.surface.blit(self.wall_image, (self.get_width()-gwidth, y))

    def draw(self, target, dest):
        target.blit(self.surface, dest)

    def get_width(self):
        return self.surface.get_width()

    def get_height(self):
        return self.surface.get_height()

if __name__ == "__main__":
    pass
