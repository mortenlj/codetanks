#!/usr/bin/env python
# -*- coding: utf-8

from nose.tools import assert_equal, raises

from ibidem.codetanks.server import events


class TestEvent(object):
    def test_event_queue_works_in_trivial_case(self):
        events.put(events.START_GAME)
        assert_equal(events.get().next(), events.START_GAME)

    @raises(StopIteration)
    def test_event_queue_does_not_block(self):
        events.get().next()

    def test_numerous_events_shows_up_in_order(self):
        es = events.Event(10), events.Event(20)
        for e in es:
            events.put(e)
        assert_equal(es, tuple(events.get()))


if __name__ == "__main__":
    import nose
    nose.main()
