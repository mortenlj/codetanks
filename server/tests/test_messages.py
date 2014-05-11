#!/usr/bin/env python
# -*- coding: utf-8

from nose.tools import eq_, assert_true

from ibidem.codetanks.server import messages


def test_existence():
    assert_true(hasattr(messages, "Registration"))
    assert_true(hasattr(messages, "GameInfo"))


def test_attributes():
    r = messages.Registration("payload_data")
    assert_true(hasattr(r, "type"))
    assert_true(hasattr(r, "payload"))
    eq_(r.type, "Registration")
    eq_(r.payload, "payload_data")

if __name__ == "__main__":
    import nose
    nose.main()
