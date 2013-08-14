#!/usr/bin/env python
# -*- coding: utf-8

"""
Placeholder for actual data provider
"""

from random import choice, randint
import pygame
from entities import Bullet
import pkg_resources

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480

bullets = pygame.sprite.RenderUpdates()

def init():
    for i in range(10):
        position = (randint(0, SCREEN_WIDTH), randint(0, SCREEN_HEIGHT))
        direction = (choice([-1, 1]), choice([-1, 1]))
        bullets.add(Bullet(position, direction))

def get():
    return bullets

if __name__ == "__main__":
    pass
