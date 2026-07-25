import numpy as np


class RayCaster:

    def __init__(self):
        pass

    def intersect_aabb(self, ray, minimum, maximum):

        minimum = np.array(minimum, dtype=float)
        maximum = np.array(maximum, dtype=float)

        t1 = (minimum - ray.origin) / ray.direction
        t2 = (maximum - ray.origin) / ray.direction

        tmin = np.maximum.reduce(
            np.minimum(t1, t2)
        )

        tmax = np.minimum.reduce(
            np.maximum(t1, t2)
        )

        if tmax >= max(tmin, 0):

            return tmin

        return None
    
    def cast(self, ray, scene_objects):

        closest_object = None

        closest_distance = float("inf")

        for obj in scene_objects:

            box = obj.bounding_box

            hit = self.intersect_aabb(

                ray,

                box.minimum,

                box.maximum

            )

            if hit is not None:

                if hit < closest_distance:

                    closest_distance = hit

                    closest_object = obj

        return closest_object