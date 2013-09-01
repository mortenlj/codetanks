#!/usr/bin/env python
# -*- coding: utf-8

from ibidem.codetanks.server.vec2d import vec2d


class Command(object):
    def __init__(self, tank):
        self.tank = tank
        self._abort = False

    def update(self, time_passed):
        if self._abort:
            return
        self._update_internal(time_passed)

    def _update_internal(self, time_passed):
        pass

    def finished(self):
        if self._abort:
            return True
        return self._finished_internal()

    def _finished_internal(self):
        return True

    def abort(self):
        self._abort = True


class Move(Command):
    speed = 0.1

    def __init__(self, tank, distance):
        super(Move, self).__init__(tank)
        self.target_position = tank.position + (tank.direction * distance)

    def _update_internal(self, time_passed):
        displacement = vec2d(
            self.tank.direction.x * self.speed * time_passed,
            self.tank.direction.y * self.speed * time_passed
        )
        self.tank.position += displacement

    def _finished_internal(self):
        return self.tank.rect.collidepoint(self.target_position)


class AngleAdjuster(Command):
    def __init__(self, tank, direction):
        super(AngleAdjuster, self).__init__(tank)
        self.direction = vec2d(direction).normalized()

    def _update_internal(self, time_passed):
        angle = self.get_vector().get_angle_between(self.direction)
        if angle:
            adjustment = self.rate * time_passed
            if abs(angle) < adjustment:
                adjustment = angle
            elif angle < 0:
                adjustment = -adjustment
            self.get_vector().rotate(adjustment)

    def _finished_internal(self):
        angle = self.get_vector().get_angle_between(self.direction)
        return abs(angle) < 0.000001


class Turn(AngleAdjuster):
    rate = 0.1

    def get_vector(self):
        return self.tank.direction


class Aim(AngleAdjuster):
    rate = 0.3

    def get_vector(self):
        return self.tank.aim


if __name__ == "__main__":
    pass
