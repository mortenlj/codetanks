#!/usr/bin/env python
# -*- coding: utf-8
import logging
import time
from datetime import datetime

import pygame
from ibidem.codetanks.domain.messages_pb2 import GameInfo, RegistrationReply, ClientType, RegistrationResult, Event, \
    GameStarted, GameOver

from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.com import ChannelType
from ibidem.codetanks.server.constants import PLAYER_COUNT, MAX_HEALTH, BULLET_DAMAGE, TANK_SPEED, ROTATION, \
    BULLET_SPEED, TANK_RADIUS, BULLET_RADIUS, CANNON_RELOAD

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
        self._event_sequence_id = 1

    def next_sequence_id(self):
        self._event_sequence_id += 1
        return self._event_sequence_id - 1

    def start(self):
        game_info = self.build_game_info()
        sequence_id = self.next_sequence_id()
        self._viewer_channel.send(Event(game_started=GameStarted(game_info=game_info), sequence_id=sequence_id))
        for bot in self._bots:
            event = Event(game_started=GameStarted(game_info=game_info, you=bot.tank.entity), sequence_id=sequence_id)
            bot.event_channel.send(event)
        self.clock = pygame.time.Clock()
        LOG.info("Game started!")

    def started(self):
        return self.clock is not None

    def game_full(self):
        return len(self._bots) == PLAYER_COUNT

    def finished(self):
        live_count = self._world.number_of_live_bots
        return len(self._bots) > 1 >= live_count

    def run(self):
        LOG.info("GameServer starting, registration available on %s", self._registration_channel.url)
        while not self.game_full():
            self._run_once()
        LOG.info("Players registered, preparing to start game")
        time.sleep(0.1)
        self.start()
        while not self.finished():
            self._run_once()
        LOG.info("Game finished, allowing %d seconds for victory celebrations", self._victory_delay.seconds)
        start = datetime.now()
        winner = self._world.get_live_bots()[-1]
        game_over = Event(game_over=GameOver(winner=winner.entity), sequence_id=self.next_sequence_id())
        for bot in self._bots:
            bot.event_channel.send(game_over)
        self._viewer_channel.send(game_over)
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
        if self.started():
            ticks = self.clock.tick(60)
            self._world.update(ticks)
        self._viewer_channel.send(Event(game_data=self._world.gamedata))
        for tank_id, events in self._world.get_events().items():
            bots = self._bots if tank_id is None else (self._bots[tank_id],)
            for event in events:
                assert isinstance(event, Event), "%r is not an instance of Event" % event
                event.sequence_id = self.next_sequence_id()
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

    def _handle_bot_registration_inner(self, registration, event_channel, cmd_channel):
        if self.game_full():
            return RegistrationReply(
                result=RegistrationResult.FAILURE,
                game_info=self.build_game_info()
            )
        tank_id = len(self._bots)
        tank = self._world.add_tank(registration.id, tank_id)
        bot = Bot(registration.id, tank_id, event_channel, cmd_channel, tank)
        self._bots.append(bot)
        self._handlers[bot.cmd_channel] = bot.handle_command
        LOG.info("Bot registered with cmd_url %s and event_url %s", cmd_channel.url, event_channel.url)
        return RegistrationReply(
            result=RegistrationResult.SUCCESS,
            game_info=self.build_game_info(),
            event_url=event_channel.url,
            cmd_url=cmd_channel.url,
            id=tank_id
        )

    def _handle_bot_registration(self, registration):
        reply = self._handle_bot_registration_inner(
            registration,
            self._channel_factory(ChannelType.PUBLISH),
            self._channel_factory(ChannelType.REPLY)
        )
        self._registration_channel.send(reply)

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
            bullet_radius=BULLET_RADIUS,
            cannon_reload=CANNON_RELOAD,
        )


if __name__ == "__main__":
    pass
