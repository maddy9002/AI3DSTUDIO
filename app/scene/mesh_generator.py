from scene.mesh import Mesh


class MeshGenerator:

    @staticmethod
    def create_cube():

        mesh = Mesh()

        mesh.vertices = [

            (-0.5,-0.5,-0.5),
            ( 0.5,-0.5,-0.5),
            ( 0.5, 0.5,-0.5),
            (-0.5, 0.5,-0.5),

            (-0.5,-0.5, 0.5),
            ( 0.5,-0.5, 0.5),
            ( 0.5, 0.5, 0.5),
            (-0.5, 0.5, 0.5)

        ]

        mesh.faces = [

            (0,1,2,3),
            (4,5,6,7),

            (0,4,7,3),
            (1,5,6,2),

            (3,2,6,7),
            (0,1,5,4)

        ]

        return mesh

    @staticmethod
    def create_plane():

        vertices = [

            (-0.5, 0.0, -0.5),
            ( 0.5, 0.0, -0.5),
            ( 0.5, 0.0,  0.5),
            (-0.5, 0.0,  0.5)

        ]

        faces = [

            (0, 1, 2, 3)

        ]

        return Mesh(vertices, faces)

    @staticmethod
    def create_sphere():
        pass

    @staticmethod
    def create_cylinder():
        pass

    @staticmethod
    def create_cone():
        pass

    @staticmethod
    def create_torus():
        pass