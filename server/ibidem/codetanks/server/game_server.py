#!/usr/bin/env python
# -*- coding: utf-8
from gevent import sleep

from goless import dcase, rcase, select
import pygame
from ibidem.codetanks.domain.ttypes import Arena, GameInfo


class GameServer(object):
    def __init__(self, game_server_channel, update_channel):
        self.input_channel = game_server_channel
        self.update_channel = update_channel
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
        print "GameServer starting"
        self.start()
        while True:
            self._run_once()

    def _run_once(self):
        case, value = select(self.cases.keys())
        if case != self.dcase:
            print "GameServer received message: %r" % value
            self.cases[case](value)
        sleep(.01)

    def _handle_input(self, value):
        print "GameServer sending game_info"
        self.update_channel.send(self.build_game_info())

    def build_game_data(self):
        game_data = {}
        return game_data

    def build_game_info(self):
        arena = Arena(self.bounds.width, self.bounds.height)
        return GameInfo(arena)


if __name__ == "__main__":
    pass
