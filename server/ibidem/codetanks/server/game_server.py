#!/usr/bin/env python
# -*- coding: utf-8

import pygame

from ibidem.codetanks.domain.ttypes import Arena, GameInfo, GameData, RegistrationReply, ClientType
from ibidem.codetanks.server.com import ChannelType


class GameServer(object):
    def __init__(self, registration_channel, viewer_channel, channel_factory):
        self._registration_channel = registration_channel
        self._viewer_channel = viewer_channel
        self._channel_factory = channel_factory
        pygame.init()
        self.bounds = pygame.Rect(0, 0, 500, 500)
        self.clock = None
        self._handlers = {
            self._registration_channel: self._handle_registration
        }
        self._bot_channels = {}

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
        received_messages = len([self._handlers[channel](channel.recv()) for channel in self._handlers.keys() if channel.ready()])
        if received_messages > 0:
            print "GameServer processed %d messages" % received_messages
        self._viewer_channel.send(self.build_game_data())
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
        self._bot_channels[registration.id] = {
            ChannelType.PUBLISH: event_channel,
            ChannelType.REPLY: cmd_channel
        }
        self._registration_channel.send(RegistrationReply(self.build_game_info(), event_channel.url, cmd_channel.url))

    def build_game_data(self):
        return GameData([], [])

    def build_game_info(self):
        arena = Arena(self.bounds.width, self.bounds.height)
        return GameInfo(arena)


if __name__ == "__main__":
    pass
