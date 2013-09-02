#!/usr/bin/env python
# -*- coding: utf-8

from Queue import Queue, Empty


class Event(object):
    def __init__(self, event_type, **kwargs):
        self.type = event_type
        self.__dict__.update(kwargs)

START_GAME = Event(1)

_queue = Queue()


def put(event):
    _queue.put(event)


def get():
    try:
        while True:
            yield _queue.get_nowait()
    except Empty:
        pass

if __name__ == "__main__":
    pass
