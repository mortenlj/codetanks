#!/usr/bin/env python
# -*- coding: utf-8

import pygame


class GameServer(object):
    def __init__(self):
        pygame.init()
        self.bounds = pygame.Rect(0, 0, 500, 500)
        self.clock = None

    def start(self):
        self.clock = pygame.time.Clock()

    def started(self):
        return self.clock is not None

    def update(self):
        pass

    def build_game_data(self):
        game_data = {}
        return game_data

    def build_game_info(self):
        return {
            "arena": {
                "width": self.bounds.width,
                "height": self.bounds.height,
            }
        }


if __name__ == "__main__":
    pass
