#!/usr/bin/env python
# -*- coding: utf-8
from Queue import Empty
import socket
from uuid import uuid4

import pygame
import zmq

from ibidem.codetanks.viewer.entities import Tank, Bullet
from ibidem.codetanks.viewer.events import Killed, Created
from ibidem.codetanks.domain.util import serialize, deserialize
from ibidem.codetanks.domain.ttypes import Registration, ClientType, Id


class ServerProxy(object):
    """Serve as a stand-in for the actual game server, so that the viewer
    doesn't have to worry about how the communication is taking place.
    Also responsible for "faking it" if the game server hasn't sent an
    update in time.
    """
    def __init__(self, server_url):
        """Initialize a new server proxy

        :param server_url: The URL of the actual server being proxied
        """
        self.tanks = pygame.sprite.RenderUpdates()
        self.bullets = pygame.sprite.RenderUpdates()
        self._tanks = {}
        self._bullets = {}
        zmq_context = zmq.Context.instance()
        registration_socket = zmq_context.socket(zmq.REQ)
        registration_socket.connect(server_url)
        registration_socket.send(serialize(Registration(ClientType.VIEWER, Id("viewer:%s:%s" % (socket.gethostname(), uuid4()), 1))))
        reply = deserialize(registration_socket.recv())
        self._update_socket = zmq_context.socket(zmq.SUB)
        self._update_socket.set(zmq.SUBSCRIBE, "")
        arena = reply.game_info.arena
        self.arena = pygame.Rect(0, 0, arena.width, arena.height)
        event_url = reply.event_url
        print "Subscribing to %s" % event_url
        self._update_socket.connect(event_url)

    def _update_entities(self, updates, entities, sprite_group, entity_class):
        to_kill = sprite_group.copy()
        for update in updates:
            entity_id = update["id"]
            if entities.has_key(entity_id):
                entity = entities[entity_id]
                entity.update_from_dict(update)
                to_kill.remove(entity)
            else:
                entity = entity_class(update)
                sprite_group.add(entity)
                entities[entity.id] = entity
                pygame.event.post(Created(entity))
        for entity in to_kill:
            entity.kill()
            pygame.event.post(Killed(entity))

    def _update_game_data(self, game_data):
        self._update_entities(game_data.tanks, self._tanks, self.tanks, Tank)
        self._update_entities(game_data.bullets, self._bullets, self.bullets, Bullet)

    def _get_server_update(self):
        return deserialize(self._update_socket.recv())

    def update(self):
        try:
            game_data = self._get_server_update()
            self._update_game_data(game_data)
        except Empty:
            pass
        return self.tanks, self.bullets


if __name__ == "__main__":
    pass
