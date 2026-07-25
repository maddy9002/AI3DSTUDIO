import math
import numpy as np

from scene.ray import Ray


class RayBuilder:

    @staticmethod
    def build_ray(mouse_x, mouse_y, viewport, camera):

        width = viewport.width()
        height = viewport.height()

        # Normalized Device Coordinates
        x = (2.0 * mouse_x) / width - 1.0
        y = 1.0 - (2.0 * mouse_y) / height

        fov = math.radians(45.0)
        aspect = width / height

        px = x * math.tan(fov / 2.0) * aspect
        py = y * math.tan(fov / 2.0)

        forward = np.array(camera.get_forward(), dtype=float)
        right = np.array(camera.get_right(), dtype=float)
        up = np.array(camera.get_up(), dtype=float)

        print("Forward:", forward)
        print("Right:", right)
        print("Up:", up)

        direction = forward + px * right + py * up

        direction = forward + px * right + py * up
        direction = direction / np.linalg.norm(direction)

        origin = np.array(camera.get_position(), dtype=float)

        return Ray(origin, direction)