import numpy as np


class Ray:

    def __init__(self, origin, direction):
        self.origin = np.array(origin, dtype=float)

        self.direction = np.array(direction, dtype=float)

        length = np.linalg.norm(self.direction)

        if length != 0:
            self.direction /= length

    def point_at(self, distance):

        return self.origin + self.direction * distance