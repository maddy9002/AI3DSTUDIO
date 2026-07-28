from scene.mesh_generator import MeshGenerator


class MeshCache:

    _cache = {}

    @classmethod
    def get_mesh(cls, primitive_type):

        if primitive_type in cls._cache:

            return cls._cache[primitive_type]

        if primitive_type == "Cube":

            mesh = MeshGenerator.create_cube()

        elif primitive_type == "Plane":

            mesh = MeshGenerator.create_plane()

        elif primitive_type == "Cylinder":

            mesh = MeshGenerator.create_cylinder()

        elif primitive_type == "Cone":

            mesh = MeshGenerator.create_cone()

        elif primitive_type == "Sphere":

            mesh = MeshGenerator.create_sphere()

        elif primitive_type == "Torus":

            mesh = MeshGenerator.create_torus()

        else:

            mesh = None

        cls._cache[primitive_type] = mesh

        return mesh