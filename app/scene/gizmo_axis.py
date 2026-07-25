from scene.bounding_box import BoundingBox


class GizmoAxis:

    def __init__(self, axis):

        self.axis = axis

        self.length = 2.0
        self.thickness = 0.08

        self.position = [0.0, 0.0, 0.0]

        self.bounding_box = BoundingBox(
            center=[0.0, 0.0, 0.0],
            size=[1.0, 1.0, 1.0]
        )

    def update(self, center):

        self.position = center

        x = center[0]
        y = center[1]
        z = center[2]

        t = self.thickness
        l = self.length

        if self.axis == "X":

            self.bounding_box.update(
                center=[
                    x + l / 2,
                    y,
                    z
                ],
                size=[
                    l,
                    t * 2,
                    t * 2
                ]
            )

        elif self.axis == "Y":

            self.bounding_box.update(
                center=[
                    x,
                    y + l / 2,
                    z
                ],
                size=[
                    t * 2,
                    l,
                    t * 2
                ]
            )

        else:

            self.bounding_box.update(
                center=[
                    x,
                    y,
                    z + l / 2
                ],
                size=[
                    t * 2,
                    t * 2,
                    l
                ]
            )