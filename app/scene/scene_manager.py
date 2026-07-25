from scene.raycast import RayCaster


class SceneManager:

    def __init__(self):

        self.scene_objects = []

        self.raycaster = RayCaster()

    def add_object(self, obj):

        self.scene_objects.append(obj)

    def remove_object(self, obj):

        if obj in self.scene_objects:
            self.scene_objects.remove(obj)

    def get_objects(self):

        return self.scene_objects