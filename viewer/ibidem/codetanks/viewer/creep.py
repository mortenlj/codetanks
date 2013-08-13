#!/usr/bin/env python
# -*- coding: utf-8

import pygame
from pygame.sprite import Sprite
from random import randint

from vec2d import vec2d

class Creep(Sprite):
    """ A creep sprite that bounces off walls and changes its
    direction from time to time.
    """
    def __init__(self, screen, img_filename, init_position, init_direction, speed):
        """ Create a new Creep.

            screen:
                The screen on which the creep lives (must be a
                pygame Surface object, such as pygame.display)

            img_filaneme:
                Image file for the creep.

            init_position:
                A vec2d or a pair specifying the initial position
                of the creep on the screen.

            init_direction:
                A vec2d or a pair specifying the initial direction
                of the creep. Must have an angle that is a
                multiple of 45 degres.

            speed:
                Creep speed, in pixels/millisecond (px/ms)
        """
        Sprite.__init__(self)
        self.screen = screen
        self.speed = speed
        self.base_image = pygame.image.load(img_filename).convert_alpha()
        self.image = self.base_image
        self.image_w, self.image_h = self.image.get_size()
        self.pos = vec2d(init_position)
        self.direction = vec2d(init_direction).normalized()
        self._counter = 0

    def update(self, time_passed):
        self._change_direction(time_passed)

        # Make the creep point in the correct direction.
        # Since our direction vector is in screen coordinates
        # (i.e. right bottom is 1, 1), and rotate() rotates
        # counter-clockwise, the angle must be inverted to
        # work correctly.
        #
        self.image = pygame.transform.rotate(self.base_image, -self.direction.angle)
        displacement = vec2d(
            self.direction.x * self.speed * time_passed,
            self.direction.y * self.speed * time_passed
        )

        self.pos += displacement

        # When the image is rotated, its size is changed.
        # We must take the size into account for detecting
        # collisions with the walls.
        #
        self.image_w, self.image_h = self.image.get_size()
        bounds_rect = self.screen.get_rect().inflate(-self.image_w, -self.image_h)

        if self.pos.x < bounds_rect.left:
            self.pos.x = bounds_rect.left
            self.direction.x *= -1
        elif self.pos.x > bounds_rect.right:
            self.pos.x = bounds_rect.right
            self.direction.x *= -1
        elif self.pos.y < bounds_rect.top:
            self.pos.y = bounds_rect.top
            self.direction.y *= -1
        elif self.pos.y > bounds_rect.bottom:
            self.pos.y = bounds_rect.bottom
            self.direction.y *= -1

    def _change_direction(self, time_passed):
        self._counter += time_passed
        if self._counter > randint(400, 500):
            self.direction.rotate(randint(-90, 90))
            self._counter = 0



    def blitme(self):
        draw_pos = self.image.get_rect().move(
            self.pos.x - self.image_w / 2,
            self.pos.y - self.image_h / 2
        )
        self.screen.blit(self.image, draw_pos)



if __name__ == "__main__":
    pass
