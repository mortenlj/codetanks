#!/usr/bin/env python
# -*- coding: utf-8

"""
Placeholder for actual data provider
"""

from random import choice, randint
from creep import Creep

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
CREEP_FILENAMES = [
    'bluecreep.png',
    'pinkcreep.png',
    'graycreep.png']
N_CREEPS = 20

creeps = []

def init(screen):
    for i in range(N_CREEPS):
        creeps.append(Creep(screen,
                            choice(CREEP_FILENAMES),
                            (   randint(0, SCREEN_WIDTH),
                                randint(0, SCREEN_HEIGHT)),
                            (   choice([-1, 1]),
                                choice([-1, 1])),
                            0.1))

def get():
    return creeps

if __name__ == "__main__":
    pass
