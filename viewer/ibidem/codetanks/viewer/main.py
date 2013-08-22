#!/usr/bin/env python
# -*- coding: utf-8

import pygame
import dummy_server
from ibidem.codetanks.viewer.server_proxy import ServerProxy

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
BG_COLOR = 20, 20, 20

def main():
    pygame.init()
    screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
    screen.fill(BG_COLOR)
    pygame.display.flip()
    background = screen.copy()

    clock = pygame.time.Clock()

    server = ServerProxy("dummy")
    server.start()

    while True:
        time_passed = clock.tick(50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Update and redraw all entities
        entity_groups = server.update(time_passed)
        updates = []
        for group in entity_groups:
            group.clear(screen, background)
            updates.extend(group.draw(screen))

        pygame.display.update(updates)


if __name__ == "__main__":
    main()
