#!/usr/bin/env python
# -*- coding: utf-8

import logging

from ibidem.codetanks.domain.messages_pb2 import CommandResult, CommandReply, BotStatus, CommandType

LOG = logging.getLogger(__name__)


class Bot(object):
    def __init__(self, bot_id, tank_id, event_channel, cmd_channel, tank):
        self.bot_id = bot_id
        self.tank_id = tank_id
        self.event_channel = event_channel
        self.cmd_channel = cmd_channel
        self.tank = tank

    def handle_command(self, command):
        LOG.debug("Handling command %r for bot %r", command, self)
        LOG.debug("Current status for %r is %r", self, self.tank.status)
        if self.tank.status != BotStatus.IDLE:
            self.cmd_channel.send(CommandReply(result=CommandResult.BUSY))
        else:
            name = CommandType.Name(command.type).lower()
            params = (command.value,) if command.HasField("value") else ()
            LOG.debug("Calling %s(%s) for bot %r", name, ", ".join(repr(x) for x in params), self)
            func = getattr(self.tank, name)
            func(*params)
            self.cmd_channel.send(CommandReply(result=CommandResult.ACCEPTED))
        LOG.debug("Status for %r after command is %r", self, self.tank.status)

    def __repr__(self):
        return "Bot(%r, %r, %r, %r)" % (self.bot_id, self.tank_id, self.event_channel, self.cmd_channel)
