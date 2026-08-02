class Mesh:

    def __init__(self, vertices=None, faces=None):

        self.vertices = []

        if vertices is not None:

            for vertex in vertices:

                self.vertices.append([
                    float(vertex[0]),
                    float(vertex[1]),
                    float(vertex[2])
                ])

        self.faces = []

        if faces is not None:

            for face in faces:

                self.faces.append(tuple(face))

        self.edges = []

        self.normals = []

        self.uvs = []

    def build_edges(self):

        edge_set = set()

        for face in self.faces:

            face = list(face)

            count = len(face)

            for i in range(count):

                a = int(face[i])
                b = int(face[(i + 1) % count])

                edge = tuple(sorted((a, b)))

                edge_set.add(edge)

        self.edges = sorted(list(edge_set))