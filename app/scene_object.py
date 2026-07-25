from scene.bounding_box import BoundingBox

class SceneObject:

    def __init__(
        self,
        name,
        object_type
    ):

        self.name = name
        self.object_type = object_type

        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1.0, 1.0, 1.0]

        self.bounding_box = BoundingBox(
            self.position,
            self.scale
        )