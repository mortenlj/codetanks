#!/usr/bin/env python
# -*- coding: utf-8
import logging
from datetime import datetime

import pygame

from ibidem.codetanks.domain.messages_pb2 import GameInfo, RegistrationReply, ClientType, RegistrationResult, Event
from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.com import ChannelType
from ibidem.codetanks.server.constants import PLAYER_COUNT, MAX_HEALTH, BULLET_DAMAGE, TANK_SPEED, ROTATION, \
    BULLET_SPEED, TANK_RADIUS, BULLET_RADIUS

LOG = logging.getLogger(__name__)


class GameServer(object):
    def __init__(self,
                 registration_channel,
                 viewer_channel,
                 channel_factory,
                 world,
                 victory_delay):
        self._registration_channel = registration_channel
        self._viewer_channel = viewer_channel
        self._channel_factory = channel_factory
        self._world = world
        pygame.init()
        self.clock = None
        self._handlers = {
            self._registration_channel: self._handle_registration
        }
        self._bots = []
        self._victory_delay = victory_delay

    def start(self):
        self.clock = pygame.time.Clock()

    def started(self):
        return self.clock is not None

    def finished(self):
        live_count = self._world.number_of_live_bots
        return len(self._bots) > 1 and live_count <= 1

    def run(self):
        LOG.info("GameServer starting, registration available on %s", self._registration_channel.url)
        while not self.finished():
            self._run_once()
        LOG.info("Game finished, allowing %d seconds for victory celebrations", self._victory_delay.seconds)
        start = datetime.now()
        while (datetime.now() - start) < self._victory_delay:
            self._run_once()

    def _run_once(self):
        received_messages = 0
        for channel in list(self._handlers.keys()):
            if channel.ready():
                self._handlers[channel](channel.recv())
                received_messages += 1
        if received_messages > 0:
            LOG.debug("GameServer processed %d messages", received_messages)
        self._viewer_channel.send(self._world.gamedata)
        if self.started():
            ticks = self.clock.tick(60)
            self._world.update(ticks)
        for tank_id, events in self._world.get_events().items():
            bots = self._bots if tank_id is None else (self._bots[tank_id],)
            for event in events:
                assert isinstance(event, Event), "%r is not an instance of Event" % event
                for bot in bots:
                    bot.event_channel.send(event)

    def _handle_registration(self, registration):
        LOG.info("GameServer received registration: %r", registration)
        if registration.client_type == ClientType.BOT:
            self._handle_bot_registration(registration)
        else:
            self._registration_channel.send(RegistrationReply(
                result=RegistrationResult.SUCCESS,
                game_info=self.build_game_info(),
                event_url=self._viewer_channel.url
            ))

    def _handle_bot_registration(self, registration):
        if self.started():
            self._registration_channel.send(RegistrationReply(
                result=RegistrationResult.FAILURE,
                game_info=self.build_game_info()
            ))
            return
        event_channel = self._channel_factory(ChannelType.PUBLISH)
        cmd_channel = self._channel_factory(ChannelType.REPLY)
        tank_id = len(self._bots)
        tank = self._world.add_tank(registration.id, tank_id)
        bot = Bot(registration.id, tank_id, event_channel, cmd_channel, tank)
        self._bots.append(bot)
        self._handlers[bot.cmd_channel] = bot.handle_command
        self._registration_channel.send(
            RegistrationReply(
                result=RegistrationResult.SUCCESS,
                game_info=self.build_game_info(),
                event_url=event_channel.url,
                cmd_url=cmd_channel.url,
                id=tank_id
            ))
        if len(self._bots) == PLAYER_COUNT:
            self.start()

    def build_game_info(self):
        return GameInfo(
            arena=self._world.arena,
            max_health=MAX_HEALTH,
            bullet_damage=BULLET_DAMAGE,
            player_count=PLAYER_COUNT,
            tank_speed=TANK_SPEED,
            rotation=ROTATION,
            bullet_speed=BULLET_SPEED,
            tank_radius=TANK_RADIUS,
            bullet_radius=BULLET_RADIUS
        )


if __name__ == "__main__":
    pass
