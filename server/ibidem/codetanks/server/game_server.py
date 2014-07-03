#!/usr/bin/env python
# -*- coding: utf-8

import pygame
from pinject import copy_args_to_internal_fields, copy_args_to_public_fields

from ibidem.codetanks.domain.ttypes import GameInfo, RegistrationReply, ClientType
from ibidem.codetanks.server.com import ChannelType


class Bot(object):
    @copy_args_to_public_fields
    def __init__(self, bot_id, tank_id, event_channel, cmd_channel):
        pass


class GameServer(object):
    @copy_args_to_internal_fields
    def __init__(self, registration_channel, viewer_channel, channel_factory, world):
        pygame.init()
        self.clock = None
        self._handlers = {
            self._registration_channel: self._handle_registration
        }
        self._bots = []

    def start(self):
        self.clock = pygame.time.Clock()

    def started(self):
        return self.clock is not None

    def update(self):
        pass

    def run(self):
        print "GameServer starting, registration available on %s" % self._registration_channel.url
        self.start()
        while self.started():
            self._run_once()

    def _run_once(self):
        received_messages = 0
        for channel in self._handlers.keys():
            if channel.ready():
                self._handlers[channel](channel.recv())
                received_messages += 1
        if received_messages > 0:
            print "GameServer processed %d messages" % received_messages
        self._viewer_channel.send(self._world.build_game_data())
        self.clock.tick(60)

    def _handle_registration(self, registration):
        print "GameServer received registration: %r" % registration
        if registration.client_type == ClientType.BOT:
            self._handle_bot_registration(registration)
        else:
            self._registration_channel.send(RegistrationReply(self.build_game_info(), self._viewer_channel.url))

    def _handle_bot_registration(self, registration):
        event_channel = self._channel_factory(ChannelType.PUBLISH)
        cmd_channel = self._channel_factory(ChannelType.REPLY)
        tank_id = len(self._bots)
        bot = Bot(registration.id, tank_id, event_channel, cmd_channel)
        self._bots.append(bot)
        self._world.add_tank(bot)
        self._registration_channel.send(RegistrationReply(self.build_game_info(), event_channel.url, cmd_channel.url))
        self._handlers[bot.cmd_channel] = self._handle_bot_cmd

    def _handle_bot_cmd(self, todo):
        pass

    def build_game_info(self):
        return GameInfo(self._world.arena)


if __name__ == "__main__":
    pass
