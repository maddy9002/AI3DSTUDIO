import math
import numpy as np

from scene.ray import Ray


class RayBuilder:

    @staticmethod
    def build_ray(
        mouse_x,
        mouse_y,
        viewport,
        camera
    ):

        width = viewport.width()
        height = viewport.height()

        if width <= 0:
            width = 1

        if height <= 0:
            height = 1

        # ---------------------------------
        # Normalized Device Coordinates
        # ---------------------------------

        x = (
            2.0 * mouse_x
        ) / width - 1.0

        y = 1.0 - (
            2.0 * mouse_y
        ) / height

        # ---------------------------------
        # Projection
        # ---------------------------------

        fov = math.radians(45.0)

        aspect = (
            float(width)
            / float(height)
        )

        tan_half_fov = math.tan(
            fov / 2.0
        )

        px = (
            x
            * tan_half_fov
            * aspect
        )

        py = (
            y
            * tan_half_fov
        )

        # ---------------------------------
        # Camera Basis
        # ---------------------------------

        forward = np.array(
            camera.get_forward(),
            dtype=np.float32
        )

        right = np.array(
            camera.get_right(),
            dtype=np.float32
        )

        up = np.array(
            camera.get_up(),
            dtype=np.float32
        )

        # ---------------------------------
        # Ray Direction
        # ---------------------------------

        direction = (
            forward
            + px * right
            + py * up
        )

        length = np.linalg.norm(
            direction
        )

        if length < 1e-8:

            direction = forward.copy()

        else:

            direction /= length

        # ---------------------------------
        # Ray Origin
        # ---------------------------------

        origin = np.array(
            camera.get_position(),
            dtype=np.float32
        )

        return Ray(
            origin,
            direction
        )