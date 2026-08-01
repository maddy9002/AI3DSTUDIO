from app.scene.bounding_box import BoundingBox


class SceneObject:

    def __init__(self, name, object_type):

        self.name = name
        self.object_type = object_type

        self.position = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0]
        self.scale = [1.0, 1.0, 1.0]

        self.mesh = None

        # --------------------------
        # Hierarchy
        # --------------------------

        self.parent = None
        self.children = []

        self.bounding_box = BoundingBox(
            self.position,
            self.scale
        )

    # ----------------------------------
    # Parenting
    # ----------------------------------

    def add_child(self, child):

        if child is self:
            return

        if child.parent is not None:

            child.parent.remove_child(child)

        child.parent = self

        if child not in self.children:

            self.children.append(child)
            
    def remove_child(self, child):

        if child in self.children:

            self.children.remove(child)

            child.parent = None

    def translate(self, dx, dy, dz):

        self.position[0] += dx
        self.position[1] += dy
        self.position[2] += dz

    # ----------------------------------
    # World Position
    # ----------------------------------

    def get_world_position(self):

        if self.parent is None:

            return self.position.copy()

        parent = self.parent.get_world_position()

        return [

            parent[0] + self.position[0],

            parent[1] + self.position[1],

            parent[2] + self.position[2]

        ]

    # ----------------------------------
    # World Rotation
    # ----------------------------------

    def get_world_rotation(self):

        if self.parent is None:

            return self.rotation.copy()

        parent = self.parent.get_world_rotation()

        return [

            parent[0] + self.rotation[0],

            parent[1] + self.rotation[1],

            parent[2] + self.rotation[2]

        ]

    # ----------------------------------
    # World Scale
    # ----------------------------------

    def get_world_scale(self):

        if self.parent is None:

            return self.scale.copy()

        parent = self.parent.get_world_scale()

        return [

            parent[0] * self.scale[0],

            parent[1] * self.scale[1],

            parent[2] * self.scale[2]

        ]