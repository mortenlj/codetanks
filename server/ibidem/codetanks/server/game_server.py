#!/usr/bin/env python
# -*- coding: utf-8

from goless import dcase, rcase, select
from pinject import copy_args_to_public_fields
import pygame


class GameServer(object):
    @copy_args_to_public_fields
    def __init__(self, input_channel, update_channel):
        pygame.init()
        self.bounds = pygame.Rect(0, 0, 500, 500)
        self.clock = None
        self.dcase = dcase()
        self.cases = {
            self.dcase: lambda x: x,
            rcase(self.input_channel): self._handle_input
        }

    def start(self):
        self.clock = pygame.time.Clock()

    def started(self):
        return self.clock is not None

    def update(self):
        pass

    def run(self):
        self.start()
        while True:
            self._run_once()

    def _run_once(self):
        case, value = select(self.cases.keys())
        if case != self.dcase:
            self.cases[case](value)

    def _handle_input(self, value):
        self.update_channel.send(self.build_game_info())

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
