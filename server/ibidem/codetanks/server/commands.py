#!/usr/bin/env python
# -*- coding: utf-8
import math
from pymunk import Vec2d


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

    def __repr__(self):
        return repr(self.__class__.__name__)


class Move(Command):
    speed = 0.1

    def __init__(self, tank, distance, tanks, walls):
        super(Move, self).__init__(tank)
        self.target_position = tank.position + (tank.direction * distance)
        self.tanks = tanks
        self.walls = walls

    # def _update_internal(self, time_passed):
    #     displacement = vec2d(
    #         self.tank.direction.x * self.speed * time_passed,
    #         self.tank.direction.y * self.speed * time_passed
    #     )
    #     collider = Collider(self.tank, self.tanks, self.walls, displacement)
    #     moved_rect, other_rect = collider.collide()
    #     if other_rect:
    #         self.abort()
    #     self.tank.rect = moved_rect
    #
    # def _finished_internal(self):
    #     return self.tank.rect.collidepoint(self.target_position)

    def __repr__(self):
        return "%r(target=%r, current=%r)" % (self.__class__.__name__, self.target_position, self.tank.position)


class AngleAdjuster(Command):
    rate = 0.0

    def __init__(self, tank, direction):
        super(AngleAdjuster, self).__init__(tank)
        self.direction = Vec2d(direction)

    def _update_internal(self, time_passed):
        angle = self.get_vector().get_angle_between(self.direction)
        if angle:
            adjustment = math.radians(self.rate) * time_passed
            if abs(angle) < adjustment:
                adjustment = angle
            elif angle < 0:
                adjustment = -adjustment
            self.set_vector(adjustment)

    def _finished_internal(self):
        angle = self.get_vector().get_angle_between(self.direction)
        return abs(angle) < 0.000001

    def get_vector(self):
        raise NotImplementedError()

    def set_vector(self, adjustment):
        raise NotImplementedError()

    def __repr__(self):
        return "%r(target=%r, current=%r)" % (self.__class__.__name__, self.direction, self.tank.direction)


class Turn(AngleAdjuster):
    rate = 0.1

    def get_vector(self):
        return self.tank.direction

    def set_vector(self, adjustment):
        v = self.tank.direction
        v.rotate(adjustment)
        self.tank.direction = v


class Aim(AngleAdjuster):
    rate = 0.3

    def get_vector(self):
        return self.tank.aim

    def set_vector(self, adjustment):
        v = self.tank.aim
        v.rotate(adjustment)
        self.tank.aim = v


if __name__ == "__main__":
    pass
