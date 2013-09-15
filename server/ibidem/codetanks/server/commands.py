#!/usr/bin/env python
# -*- coding: utf-8
import math
from pymunk import Vec2d
import pymunk


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

    def log(self, msg):
        print "[%s] %s" % (self.tank, msg)

    def __repr__(self):
        return repr(self.__class__.__name__)


class Move(Command):
    speed = 0.1

    def __init__(self, space, tank, distance):
        super(Move, self).__init__(tank)
        self.space = space
        movement = tank.direction
        movement.length = distance
        self.target = pymunk.Body()
        self.target.position = movement + tank.position
        self._started = False
        self._finished = False

    def _update_internal(self, time_passed):
        if not self._started:
            self.tshape = pymunk.Circle(self.target, 1)
            self.tshape.sensor = True
            self.tshape.collision_type = self.tank.collision_type + 10
            self.constraint = pymunk.DampedSpring(self.tank.body, self.target, (0, 0), (0, 0), 0, 2.0, 2.0)
            to_add = (self.tshape, self.constraint)
            self.log("Adding %s to space" % ", ".join((repr(x) for x in to_add)))
            self.space.add(*to_add)
            self.log("Adding collision handler %r => %r" % (self.tank.collision_type, self.tshape.collision_type))
            self.space.add_collision_handler(self.tank.collision_type, self.tshape.collision_type, self.on_collision)
            self._started = True

    def on_collision(self, space, arbiter, *args, **kwargs):
        self.tank.body.reset_forces()
        self.tank.body.velocity = (0, 0)
        to_remove = [self.tshape]
        to_remove.extend(self.tank.body.constraints)
        self.log("Removing %s from space" % ", ".join((repr(x) for x in to_remove)))
        space.remove(*to_remove)
        self._finished = True
        return False

    def _finished_internal(self):
        self.log("Current force: %r, torque: %r, velocity: %r" % (
            self.tank.body.force,
            self.tank.body.torque,
            self.tank.body.torque))
        if self._finished:
            self.log("Removing collision handler %r => %r" % (self.tank.collision_type, self.tshape.collision_type))
            self.space.remove_collision_handler(self.tank.collision_type, self.tshape.collision_type)
            return True
        return False

    def __repr__(self):
        return "%r(target=%r, current=%r)" % (self.__class__.__name__, self.target.position, self.tank.position)


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
