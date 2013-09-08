#!/usr/bin/env python
# -*- coding: utf-8
from random import shuffle


class Collider(object):
    bullet_damage = 5

    def __init__(self, tanks, bullets, wall):
        shuffle(tanks)
        self.tanks = tanks
        self.bullets = bullets
        self.wall = wall

    def _handle_bullet_hit_tanks(self, bullet, idx):
        for i in idx:
            tank = self.tanks[i]
            if bullet.parent != tank:
                tank.health -= self.bullet_damage

    def _hit_wall(self, rect):
        return not self.wall.contains(rect)

    def collide_bullets(self):
        tank_rects = [tank.rect for tank in self.tanks]
        for bullet in self.bullets:
            idx = bullet.rect.collidelistall(tank_rects)
            self._handle_bullet_hit_tanks(bullet, idx)
            if idx or self._hit_wall(bullet.rect):
                bullet.kill()

    def collide_tanks(self):
        rects = [tank.rect for tank in self.tanks]
        for tank in self.tanks:
            idx = tank.rect.collidelistall(rects)
            if idx:
                hit_rects = [self.tanks[i].rect for i in idx]
                tank.backup(hit_rects)
            if self._hit_wall(tank.rect):
                tank.clamp()

    def collide(self):
        self.collide_bullets()
        self.collide_tanks()


if __name__ == "__main__":
    pass
