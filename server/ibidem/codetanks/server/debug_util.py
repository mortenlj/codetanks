#!/usr/bin/env python
# -*- coding: utf-8
import math

from cairocffi import SVGSurface, Context


def _id_generator():
    i = 0
    while True:
        yield i
        i += 1

_debug_generator = _id_generator()


class Plot(object):
    red = (1., 0., 0.)
    green = (0., 1., 0.)
    blue = (0., 0., 1.)
    yellow = (1., 1., 0.)
    cyan = (0., 1., 1.)
    magenta = (1., 0., 1.)

    def __init__(self, width, height):
        self.plot_id = _debug_generator.next()
        self._surface = SVGSurface("debug_plot-%05d.svg" % self.plot_id, width, height)
        self._ctx = Context(self._surface)
        self._ctx.set_source_rgb(0., 0., 0.)
        self._ctx.paint()

    def line(self, line, color):
        ctx = self._ctx
        ctx.move_to(line.p1.x, line.p1.y)
        ctx.line_to(line.p2.x, line.p2.y)
        ctx.set_source_rgb(*color)
        ctx.stroke()

    def circle(self, center, radius, stroke_color, fill_color=None):
        ctx = self._ctx
        ctx.new_sub_path()
        ctx.arc(center.x, center.y, radius, 0, math.pi*2)
        ctx.set_source_rgb(*stroke_color)
        if fill_color:
            ctx.stroke_preserve()
            ctx.set_source_rgb(*fill_color)
            ctx.fill()
        else:
            ctx.stroke()


class ScanPlot(Plot):
    def __init__(self, width, height, left, right, center, radius, tank):
        super(ScanPlot, self).__init__(width, height)
        self._left = left
        self._right = right
        self._center = center
        self._radius = radius
        self._tank = tank

    def plot(self):
        self.line(self._left, self.red)
        self.line(self._right, self.blue)
        self.line(self._center, self.green)
        self.circle(self._tank.position, self._tank.radius, self.green, self.yellow)
        self.circle(self._center.p, self._radius, self.cyan)
        self._surface.finish()

if __name__ == "__main__":
    pass
