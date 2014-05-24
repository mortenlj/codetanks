#!/usr/bin/env python
# -*- coding: utf-8

from nose.tools import eq_

from ibidem.codetanks.domain.ttypes import GameInfo, Arena
from ibidem.codetanks.domain.util import serialize, deserialize


class TestSerialization():
    def test_back_and_forth(self):
        gi = GameInfo(Arena(10, 90))
        data = serialize(gi)
        eq_(gi, deserialize(data))


if __name__ == "__main__":
    import nose
    nose.main()
