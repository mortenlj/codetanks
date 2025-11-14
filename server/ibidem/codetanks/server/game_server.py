#!/usr/bin/env python
# -*- coding: utf-8
import logging
import time
from datetime import datetime

import pygame
from ibidem.codetanks.domain.messages_pb2 import GameInfo, RegistrationReply, ClientType, RegistrationResult, Event, \
    GameStarted, GameOver

from ibidem.codetanks.server.bot import Bot
from ibidem.codetanks.server.constants import PLAYER_COUNT, MAX_HEALTH, BULLET_DAMAGE, TANK_SPEED, ROTATION, \
    BULLET_SPEED, TANK_RADIUS, BULLET_RADIUS, CANNON_RELOAD
from ibidem.codetanks.server.peer import Peer

LOG = logging.getLogger(__name__)


class GameServer(object):
    def __init__(self,
                 world,
                 victory_delay):
        self._world = world
        pygame.init()
        self.clock = None
        self._bots = []
        self._viewers = []
        self._victory_delay = victory_delay
        self._event_sequence_id = 1

    def _send_viewer_event(self, event: Event):
        for viewer in self._viewers:
            assert isinstance(viewer, Peer)
            viewer.handle_event(event)

    def next_sequence_id(self):
        self._event_sequence_id += 1
        return self._event_sequence_id - 1

    def start(self):
        game_info = self.build_game_info()
        sequence_id = self.next_sequence_id()
        self._send_viewer_event(Event(game_started=GameStarted(game_info=game_info), sequence_id=sequence_id))
        for peer, bot in self._bots:
            event = Event(game_started=GameStarted(game_info=game_info, you=bot.tank.entity), sequence_id=sequence_id)
            peer.handle_event(event)
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
        LOG.info("GameServer starting")
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
        for peer, bot in self._bots:
            peer.handle_event(game_over)
        self._send_viewer_event(game_over)
        while (datetime.now() - start) < self._victory_delay:
            self._run_once()

    def _run_once(self):
        received_commands = 0
        for peer, bot in self._bots:
            cmd = peer.next_command()
            if cmd:
                reply = bot.handle_command(cmd)
                peer.command_reply(reply)
                received_commands += 1
        if received_commands > 0:
            LOG.debug("GameServer processed %d commands", received_commands)
        if self.started():
            ticks = self.clock.tick(60)
            self._world.update(ticks)
        self._send_viewer_event(Event(game_data=self._world.gamedata))
        for tank_id, events in self._world.get_events().items():
            bots = self._bots if tank_id is None else (self._bots[tank_id],)
            for event in events:
                assert isinstance(event, Event), "%r is not an instance of Event" % event
                event.sequence_id = self.next_sequence_id()
                for peer, _ in bots:
                    peer.handle_event(event)

    def add_peer(self, peer: Peer) -> RegistrationReply:
        LOG.info("GameServer received peer: %r", peer)
        if peer.client_type == ClientType.BOT:
            return self._register_bot(peer)
        else:
            self._viewers.append(peer)
            return RegistrationReply(
                result=RegistrationResult.SUCCESS,
                game_info=self.build_game_info(),
            )

    def _register_bot(self, peer: Peer):
        if self.game_full():
            return RegistrationReply(
                result=RegistrationResult.FAILURE,
                game_info=self.build_game_info()
            )
        tank_id = len(self._bots)
        tank = self._world.add_tank(peer.id, tank_id)
        bot = Bot(peer.id, tank_id, tank)
        self._bots.append((peer, bot))
        LOG.info("Bot %r registered with peer %r", bot, peer)
        return RegistrationReply(
            result=RegistrationResult.SUCCESS,
            game_info=self.build_game_info(),
            id=tank_id
        )

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
