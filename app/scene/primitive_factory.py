from scene_object import SceneObject
from scene.mesh_cache import MeshCache


class PrimitiveFactory:

    @staticmethod
    def create(name, primitive_type):

        obj = SceneObject(name, primitive_type)

        obj.mesh = MeshCache.get_mesh(primitive_type)

        return obj