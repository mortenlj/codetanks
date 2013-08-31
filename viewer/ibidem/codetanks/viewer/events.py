#!/usr/bin/env python
# -*- coding: utf-8

import pygame

def _event_type_generator():
    i = pygame.USEREVENT + 1
    while True:
        yield i
        i += 1
_event_series = _event_type_generator()

CREATED = _event_series.next()
KILLED = _event_series.next()


def Created(entity):
    return pygame.event.Event(CREATED, entity=entity)


def Killed(entity):
    return pygame.event.Event(KILLED, entity=entity)


if __name__ == "__main__":
    pass
