#!/usr/bin/env python
# -*- coding: utf-8


class _Message(object):
    def __init__(self, payload):
        self._payload = payload
        super(_Message, self).__init__()

    @property
    def payload(self):
        return self._payload

    @property
    def type(self):
        return self.__class__.__name__


for clsname in ("Registration", "GameInfo"):
    globals()[clsname] = type(clsname, (_Message,), {})

if __name__ == "__main__":
    pass
