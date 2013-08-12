#!/usr/bin/env python
# -*- coding: utf-8

import pygame
from random import choice, randint
from creep import Creep

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
BG_COLOR = 20, 20, 20
CREEP_FILENAMES = [
    'bluecreep.png',
    'pinkcreep.png',
    'graycreep.png']
N_CREEPS = 20

def main():
    pygame.init()
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    clock = pygame.time.Clock()

    creeps = []
    for i in range(N_CREEPS):
        creeps.append(Creep(screen,
                            choice(CREEP_FILENAMES),
                            (   randint(0, SCREEN_WIDTH),
                                randint(0, SCREEN_HEIGHT)),
                            (   choice([-1, 1]),
                                choice([-1, 1])),
                            0.1))

    while True:
        time_passed = clock.tick(50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        screen.fill(BG_COLOR)

        # Update and redraw all creeps
        for creep in creeps:
            creep.update(time_passed)
            creep.blitme()

        pygame.display.flip()



if __name__ == "__main__":
    main()
