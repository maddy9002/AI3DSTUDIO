from scene.mesh import Mesh
import math

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

        segments = 24

        vertices = []
        faces = []

        # Bottom Ring

        for i in range(segments):

            angle = (2 * math.pi * i) / segments

            x = math.cos(angle) * 0.5
            z = math.sin(angle) * 0.5

            vertices.append((x, -0.5, z))

        # Top Ring

        for i in range(segments):

            angle = (2 * math.pi * i) / segments

            x = math.cos(angle) * 0.5
            z = math.sin(angle) * 0.5

            vertices.append((x, 0.5, z))

        # Bottom Center
        bottom_center = len(vertices)
        vertices.append((0.0, -0.5, 0.0))

        # Top Center
        top_center = len(vertices)
        vertices.append((0.0, 0.5, 0.0))

        # Side Faces

        for i in range(segments):

            a = i
            b = (i + 1) % segments
            c = b + segments
            d = a + segments

            faces.append((a, b, c, d))

        # Bottom Cap

        for i in range(segments):

            a = i
            b = (i + 1) % segments

            faces.append((bottom_center, b, a))

        # Top Cap

        for i in range(segments):

            a = i + segments
            b = ((i + 1) % segments) + segments

            faces.append((top_center, a, b))

        return Mesh(vertices, faces)

    @staticmethod
    def create_cone():

        segments = 24

        vertices = []
        faces = []

        # Base Ring

        for i in range(segments):

            angle = (2 * math.pi * i) / segments

            x = math.cos(angle) * 0.5
            z = math.sin(angle) * 0.5

            vertices.append((x, -0.5, z))

        # Apex

        apex = len(vertices)
        vertices.append((0.0, 0.5, 0.0))

        # Base Center

        center = len(vertices)
        vertices.append((0.0, -0.5, 0.0))

        # Side Triangles

        for i in range(segments):

            a = i
            b = (i + 1) % segments

            faces.append((a, b, apex))

        # Base

        for i in range(segments):

            a = i
            b = (i + 1) % segments

            faces.append((center, b, a))

        return Mesh(vertices, faces)
    
    @staticmethod
    def create_torus():
        pass