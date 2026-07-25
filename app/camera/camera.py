from OpenGL.GLU import gluLookAt
import math
import numpy as np

class Camera:

    def __init__(self):

        self.target = [0.0, 0.0, 0.0]

        self.distance = 5.0

        self.yaw = 0.0

        self.pitch = 20.0

    def apply(self):

        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)

        x = self.target[0] + self.distance * math.cos(pitch) * math.sin(yaw)

        y = self.target[1] + self.distance * math.sin(pitch)

        z = self.target[2] + self.distance * math.cos(pitch) * math.cos(yaw)

        gluLookAt(

            x,
            y,
            z,

            self.target[0],
            self.target[1],
            self.target[2],

            0,
            1,
            0

        )

    def get_position(self):

        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)

        x = self.target[0] + self.distance * math.cos(pitch) * math.sin(yaw)
        y = self.target[1] + self.distance * math.sin(pitch)
        z = self.target[2] + self.distance * math.cos(pitch) * math.cos(yaw)

        return [x, y, z]

    def get_forward(self):

        position = self.get_position()

        forward = [
            self.target[0] - position[0],
            self.target[1] - position[1],
            self.target[2] - position[2]
        ]

        length = math.sqrt(
            forward[0] ** 2 +
            forward[1] ** 2 +
            forward[2] ** 2
        )

        return [
            forward[0] / length,
            forward[1] / length,
            forward[2] / length
        ]

    def get_right(self):

        forward = np.array(self.get_forward(), dtype=float)
        world_up = np.array([0.0, 1.0, 0.0], dtype=float)

        right = np.cross(forward, world_up)

        length = np.linalg.norm(right)

        if length != 0:
            right /= length

        return right.tolist()

    def get_up(self):

        forward = np.array(self.get_forward(), dtype=float)
        right = np.array(self.get_right(), dtype=float)

        up = np.cross(right, forward)
        
        length = np.linalg.norm(up)

        if length != 0:
            up /= length

        return up.tolist()