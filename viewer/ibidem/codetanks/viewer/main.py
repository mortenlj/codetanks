#!/usr/bin/env python
# -*- coding: utf-8

import pygame

from ibidem.codetanks.domain.constants import PLAYER_COUNT
from ibidem.codetanks.viewer.server_proxy import ServerProxy
from ibidem.codetanks.viewer.widgets import Arena, TankInfo


BG_COLOR = 20, 20, 20


def initialize_and_display_splash():
    pygame.init()
    screen = pygame.display.set_mode((320, 200))
    rect = screen.get_rect()
    font = pygame.font.Font(None, 20)
    text = font.render("Initializing, please wait...", True, (255, 255, 255))
    textRect = text.get_rect()
    x = rect.centerx - (textRect.width / 2)
    y = rect.centery - (textRect.height / 2)
    textRect.topleft = (x, y)
    screen.blit(text, textRect)
    pygame.display.flip()


def initialize_main():
    import sys

    server_url = sys.argv[1]
    server = ServerProxy(server_url)
    arena = Arena(server.arena.width, server.arena.height)
    screen = pygame.display.set_mode([arena.get_width() + 256, arena.get_height()])
    screen.fill(BG_COLOR)
    arena.draw(screen, (0, 0))
    pygame.display.flip()
    return arena, screen, server


def draw_tank_info_widgets(arena, screen, tank_infos):
    for i in range(PLAYER_COUNT):
        if i in tank_infos:
            tank_info = tank_infos[i]
            y = 80 * i + 16
            tank_info.draw(screen, (arena.get_width(), y))


def draw_arena(arena, screen):
    arena.draw(screen, (0, 0))


def draw_entities(arena, entities):
    entities.clear(arena.game_field, arena.background)
    entities.draw(arena.game_field)


def update(server, tank_infos):
    tanks, entities = server.update()
    for tank in tanks:
        if tank.id in tank_infos:
            ti = tank_infos[tank.id]
            ti.tank = tank
        else:
            tank_infos[tank.id] = TankInfo(tank)
    return entities, tank_infos


def main():
    initialize_and_display_splash()
    arena, screen, server = initialize_main()
    tank_infos = {}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        entities, tank_infos = update(server, tank_infos)

        draw_entities(arena, entities)
        draw_tank_info_widgets(arena, screen, tank_infos)
        draw_arena(arena, screen)

        pygame.display.flip()


if __name__ == "__main__":
    main()
