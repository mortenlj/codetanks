#!/usr/bin/env python
# -*- coding: utf-8

"""
Placeholder for actual data provider
"""

from random import choice, randint
from creep import Creep
import pkg_resources

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
CREEP_FILENAMES = [
    pkg_resources.resource_filename("ibidem.codecreeps.viewer.resources", 'mockup_tank1.png'),
    pkg_resources.resource_filename("ibidem.codecreeps.viewer.resources", 'mockup_tank2.png'),
    pkg_resources.resource_filename("ibidem.codecreeps.viewer.resources", 'mockup_tank3.png')]
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
