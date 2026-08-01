from copy import deepcopy

from app.scene_object import SceneObject
from app.scene.mesh_cache import MeshCache


class PrimitiveFactory:

    @staticmethod
    def create(name, primitive_type):

        obj = SceneObject(name, primitive_type)

        obj.mesh = deepcopy(
            MeshCache.get_mesh(primitive_type)
        )

        print(f"{name}")
        print("Mesh ID:", id(obj.mesh))
        print("Vertices ID:", id(obj.mesh.vertices))

        return obj