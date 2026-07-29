class Mesh:

    def __init__(self, vertices=None, faces=None):

        self.vertices = vertices if vertices is not None else []

        self.faces = faces if faces is not None else []

        self.edges = []

        self.normals = []

        self.uvs = []

    def build_edges(self):

        edge_set = set()

        for face in self.faces:

            count = len(face)

            for i in range(count):

                a = face[i]
                b = face[(i + 1) % count]

                edge = tuple(sorted((a, b)))

                edge_set.add(edge)

        self.edges = list(edge_set)

