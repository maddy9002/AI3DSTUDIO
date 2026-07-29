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

        # ---------------------------------
        # Build Edge List
        # ---------------------------------

        mesh.build_edges()

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

        mesh = Mesh(vertices, faces)

        mesh.build_edges()

        return mesh

    @staticmethod
    def create_sphere():

        import math
        from scene.mesh import Mesh

        radius = 0.5
        stacks = 16
        sectors = 24

        vertices = []
        faces = []

        for i in range(stacks + 1):

            stack_angle = math.pi / 2 - i * math.pi / stacks

            xy = radius * math.cos(stack_angle)
            y = radius * math.sin(stack_angle)

            for j in range(sectors + 1):

                sector_angle = 2 * math.pi * j / sectors

                x = xy * math.cos(sector_angle)
                z = xy * math.sin(sector_angle)

                vertices.append((x, y, z))

        for i in range(stacks):

            k1 = i * (sectors + 1)
            k2 = k1 + sectors + 1

            for j in range(sectors):

                if i != 0:

                    faces.append((
                        k1 + j,
                        k2 + j,
                        k2 + j + 1,
                        k1 + j + 1
                    ))

                elif i == 0:

                    faces.append((
                        k1 + j,
                        k2 + j,
                        k2 + j + 1
                    ))

                if i != stacks - 1:

                    continue

                faces.append((
                    k1 + j,
                    k2 + j,
                    k1 + j + 1
                ))

        mesh = Mesh(vertices, faces)

        mesh.build_edges()

        return mesh

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

        mesh = Mesh(vertices, faces)

        mesh.build_edges()

        return mesh

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

        mesh = Mesh(vertices, faces)

        mesh.build_edges()

        return mesh
    
    @staticmethod
    def create_torus():

        major_radius = 0.6
        minor_radius = 0.2

        major_segments = 32
        minor_segments = 16

        vertices = []
        faces = []

        for i in range(major_segments):

            theta = 2 * math.pi * i / major_segments

            cos_theta = math.cos(theta)
            sin_theta = math.sin(theta)

            for j in range(minor_segments):

                phi = 2 * math.pi * j / minor_segments

                cos_phi = math.cos(phi)
                sin_phi = math.sin(phi)

                x = (major_radius + minor_radius * cos_phi) * cos_theta
                y = minor_radius * sin_phi
                z = (major_radius + minor_radius * cos_phi) * sin_theta

                vertices.append((x, y, z))

        for i in range(major_segments):

            for j in range(minor_segments):

                a = i * minor_segments + j
                b = ((i + 1) % major_segments) * minor_segments + j
                c = ((i + 1) % major_segments) * minor_segments + ((j + 1) % minor_segments)
                d = i * minor_segments + ((j + 1) % minor_segments)

                faces.append((a, b, c, d))

        mesh = Mesh(vertices, faces)

        mesh.build_edges()

        return mesh