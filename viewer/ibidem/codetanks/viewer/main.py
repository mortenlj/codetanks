#!/usr/bin/env python
# -*- coding: utf-8

import pygame
import entity_provider

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
BG_COLOR = 20, 20, 20

def main():
    pygame.init()
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    clock = pygame.time.Clock()

    entity_provider.init()

    while True:
        time_passed = clock.tick(50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        screen.fill(BG_COLOR)

        # Update and redraw all creeps
        render_updates = entity_provider.get()
        for ru in render_updates:
            ru.update(time_passed)
            ru.draw(screen)

        pygame.display.flip()



if __name__ == "__main__":
    main()
