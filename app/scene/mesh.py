class Mesh:

    def __init__(self, vertices=None, faces=None):

        self.vertices = vertices if vertices is not None else []

        self.faces = faces if faces is not None else []

        self.normals = []

        self.uvs = []