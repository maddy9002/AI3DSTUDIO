import numpy as np


class BoundingBox:

    def __init__(self, center, size):

        self.center = np.array(center, dtype=float)

        self.size = np.array(size, dtype=float)

    @property
    def minimum(self):

        return self.center - self.size / 2

    @property
    def maximum(self):

        return self.center + self.size / 2

    def update(self, center, size=None):

        self.center = np.array(center, dtype=float)

        if size is not None:
            self.size = np.array(size, dtype=float)