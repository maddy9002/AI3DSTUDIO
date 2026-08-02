from copy import deepcopy

from app.scene.mesh_generator import MeshGenerator


class MeshCache:

    _cache = {}

    @classmethod
    def get_mesh(cls, primitive_type):

        if primitive_type not in cls._cache:

            if primitive_type == "Cube":

                cls._cache[primitive_type] = MeshGenerator.create_cube()

            elif primitive_type == "Plane":

                cls._cache[primitive_type] = MeshGenerator.create_plane()

            elif primitive_type == "Cylinder":

                cls._cache[primitive_type] = MeshGenerator.create_cylinder()

            elif primitive_type == "Cone":

                cls._cache[primitive_type] = MeshGenerator.create_cone()

            elif primitive_type == "Sphere":

                cls._cache[primitive_type] = MeshGenerator.create_sphere()

            elif primitive_type == "Torus":

                cls._cache[primitive_type] = MeshGenerator.create_torus()

            else:

                return None

        # Always return a deep copy so every object owns its own mesh
        return deepcopy(cls._cache[primitive_type])

    @classmethod
    def clear(cls):

        cls._cache.clear()