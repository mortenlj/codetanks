#!/usr/bin/env python
# -*- coding: utf-8

import pygame
from ibidem.codetanks.viewer.server_proxy import ServerProxy
from ibidem.codetanks.viewer.widgets import Arena

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BG_COLOR = 20, 20, 20


def main():
    import sys
    server_url = sys.argv[1]
    server = ServerProxy(server_url)
    pygame.init()
    #TODO: Show splash while setting up, then change mode after we know how large the arena is
    screen = pygame.display.set_mode([server.arena.width + 200, server.arena.height+64])
    arena = Arena(server.arena.width, server.arena.height)
    screen.fill(BG_COLOR)
    arena.draw(screen, (0, 0))
    pygame.display.flip()

    clock = pygame.time.Clock()

    while True:
        time_passed = clock.tick(50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Update and redraw all entities
        entity_groups = server.update(time_passed)
        for group in entity_groups:
            group.clear(arena.game_field, arena.background)
            group.draw(arena.game_field)

        arena.draw(screen, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
