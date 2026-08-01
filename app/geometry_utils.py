import numpy as np

class GeometryUtils:

    @staticmethod
    def closest_point_on_segment(
        point,
        a,
        b
    ):

        ab = b - a

        length_squared = np.dot(ab, ab)

        if length_squared == 0:

            return a

        t = np.dot(point - a, ab) / length_squared

        t = max(
            0.0,
            min(
                1.0,
                t
            )
        )

        return a + ab * t

    @staticmethod
    def distance_ray_to_segment(
        ray,
        a,
        b
    ):

        ab = b - a
        ao = ray.origin - a

        u = ray.direction
        v = ab

        w0 = ray.origin - a

        a1 = np.dot(u, u)
        b1 = np.dot(u, v)
        c1 = np.dot(v, v)
        d1 = np.dot(u, w0)
        e1 = np.dot(v, w0)

        denom = a1 * c1 - b1 * b1

        if abs(denom) < 1e-6:
            return 999999.0

        s = (b1 * e1 - c1 * d1) / denom
        t = (a1 * e1 - b1 * d1) / denom

        s = max(0.0, s)
        t = max(0.0, min(1.0, t))

        closest_ray = ray.origin + u * s
        closest_seg = a + v * t

        return np.linalg.norm(
            closest_ray - closest_seg
        )