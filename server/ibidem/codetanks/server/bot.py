#!/usr/bin/env python
# -*- coding: utf-8
from pinject import copy_args_to_public_fields

if __name__ == "__main__":
    pass


class Bot(object):
    @copy_args_to_public_fields
    def __init__(self, bot_id, tank_id, event_channel, cmd_channel):
        pass

    def __repr__(self):
        return "Bot(%r, %r, %r, %r)" % (self.bot_id, self.tank_id, self.event_channel, self.cmd_channel)
