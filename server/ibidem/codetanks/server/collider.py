#!/usr/bin/env python
# -*- coding: utf-8
from ibidem.codetanks.server.vec2d import vec2d


class Collider(object):
    bullet_damage = 5

    def __init__(self, tank, tanks, walls, displacement):
        self.tank = tank
        self.collidables = [t.rect for t in tanks if t != tank]
        self.collidables.extend(walls)
        self.displacement = displacement

    def collide(self):
        idx = self.tank.rect.collidelist(self.collidables)
        if idx >= 0:
            print "ERROR: Already colliding! %s hits %s" % (self.tank.rect, self.collidables[idx])
            moved_rect = self.tank.rect
        else:
            moved_rect, idx = self._collide(vec2d(0.0, 0.0), self.displacement)
        return moved_rect, (self.collidables[idx] if idx >= 0 else None)

    def _collide(self, current_displacement, additional_displacement, old_idx=-1):
        new_displacement = current_displacement + additional_displacement
        moved_rect = self.tank.rect.move(new_displacement.x, new_displacement.y)
        adjustment = abs(additional_displacement) / 2.0
        idx = moved_rect.collidelist(self.collidables)
        if idx >= 0:
            if adjustment.length < 0.00001:
                return moved_rect, idx
            return self._collide(new_displacement, adjustment * -1.0, idx)
        else:
            if adjustment.length < 1.0:
                return moved_rect, old_idx
            return self._collide(new_displacement, adjustment, old_idx)


if __name__ == "__main__":
    pass
