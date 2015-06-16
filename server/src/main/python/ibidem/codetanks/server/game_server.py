#!/usr/bin/env python
# -*- coding: utf-8
from datetime import datetime
from functools import partial
import logging

import pygame
from pinject import copy_args_to_internal_fields
from ibidem.codetanks.domain.constants import PLAYER_COUNT
from ibidem.codetanks.domain.ttypes import GameInfo, RegistrationReply, ClientType, CommandResult, CommandReply, BotStatus, \
    RegistrationResult, CommandType, Event
from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.com import ChannelType


LOG = logging.getLogger(__name__)


class GameServer(object):
    @copy_args_to_internal_fields
    def __init__(self,
                 registration_channel,
                 viewer_channel,
                 channel_factory,
                 world,
                 victory_delay):
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
        for channel in self._handlers.keys():
            if channel.ready():
                self._handlers[channel](channel, channel.recv())
                received_messages += 1
        if received_messages > 0:
            LOG.debug("GameServer processed %d messages", received_messages)
        self._viewer_channel.send(self._world.gamedata)
        if self.started():
            ticks = self.clock.tick(60)
            self._world.update(ticks)
        for tank_id, events in self._world.get_events().iteritems():
            bots = self._bots if tank_id is None else (self._bots[tank_id],)
            for event in events:
                assert isinstance(event, Event), "%r is not an instance of Event" % event
                for bot in bots:
                    bot.event_channel.send(event)

    def _handle_registration(self, reply_channel, registration):
        LOG.debug("GameServer received registration: %r", registration)
        if registration.client_type == ClientType.BOT:
            self._handle_bot_registration(reply_channel, registration)
        else:
            reply_channel.send(RegistrationReply(RegistrationResult.SUCCESS, self.build_game_info(), self._viewer_channel.url))

    def _handle_bot_registration(self, reply_channel, registration):
        if self.started():
            reply_channel.send(RegistrationReply(RegistrationResult.FAILURE, self.build_game_info()))
            return
        event_channel = self._channel_factory(ChannelType.PUBLISH)
        cmd_channel = self._channel_factory(ChannelType.REPLY)
        tank_id = len(self._bots)
        bot = Bot(registration.id, tank_id, event_channel, cmd_channel)
        self._bots.append(bot)
        self._world.add_tank(bot)
        self._handlers[bot.cmd_channel] = partial(self._handle_bot_cmd, bot)
        reply_channel.send(RegistrationReply(RegistrationResult.SUCCESS, self.build_game_info(), event_channel.url, cmd_channel.url, tank_id))
        if len(self._bots) == PLAYER_COUNT:
            self.start()

    def _handle_bot_cmd(self, bot, reply_channel, command):
        LOG.debug("Handling command %r for bot %r", command, bot)
        LOG.debug("Current status for %r is %r", bot, self._world.tank_status(bot.tank_id))
        if self._world.tank_status(bot.tank_id) != BotStatus.IDLE:
            reply_channel.send(CommandReply(CommandResult.BUSY))
        else:
            name = CommandType._VALUES_TO_NAMES[command.type].lower()
            params = () if command.value is None else (command.value,)
            LOG.debug("Calling self._world.command(%r, %r, %s) for bot %r", bot.tank_id, name, ", ".join(repr(x) for x in params), bot)
            self._world.command(bot.tank_id, name, *params)
            reply_channel.send(CommandReply(CommandResult.OK))
        LOG.debug("Status for %r after command is %r", bot, self._world.tank_status(bot.tank_id))

    def build_game_info(self):
        return GameInfo(self._world.arena)


if __name__ == "__main__":
    pass
