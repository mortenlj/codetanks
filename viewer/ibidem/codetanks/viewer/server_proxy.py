#!/usr/bin/env python
# -*- coding: utf-8
from Queue import Empty
import socket
from uuid import uuid4

import pygame
import zmq

from ibidem.codetanks.viewer.entities import Tank, Bullet
from ibidem.codetanks.domain.util import serialize, deserialize
from ibidem.codetanks.domain.ttypes import Registration, ClientType, Id, BotStatus


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
        self.entities = pygame.sprite.LayeredUpdates()
        self.tanks = pygame.sprite.Group()

    def _update_entities(self, updates, sprite_group, entity_class):
        for update in updates:
            entity = entity_class(update)
            entity.update_visuals()
            if hasattr(entity, "status") and entity.status == BotStatus.DEAD:
                sprite_group.add(entity, layer=1)
            else:
                sprite_group.add(entity)

    def _update_game_data(self, game_data):
        self.entities.empty()
        self._update_entities(game_data.tanks, self.entities, Tank)
        self.tanks = self.entities.copy()
        self._update_entities(game_data.bullets, self.entities, Bullet)

    def _get_server_update(self):
        events = self._update_socket.poll(100)
        if events == zmq.POLLIN:
            return deserialize(self._update_socket.recv())
        raise Empty()

    def update(self):
        try:
            game_data = self._get_server_update()
            self._update_game_data(game_data)
        except Empty:
            pass
        return self.tanks, self.entities


if __name__ == "__main__":
    pass
