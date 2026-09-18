from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt
from scene.gizmo import MoveGizmo
from OpenGL.GL import *
from OpenGL.GLU import *
from scene.ray_builder import RayBuilder
from PySide6.QtGui import QImage
from PySide6.QtGui import QPainter
import cv2
from camera.camera import Camera
from scene.ray import Ray
from scene.raycast import RayCaster
import numpy as np
from scene.rotate_gizmo import RotateGizmo  
from scene.scale_gizmo import ScaleGizmo
from scene.tool_manager import ToolManager
from app.scene.selection_manager import SelectionManager
from scene.mesh_renderer import MeshRenderer
from PySide6.QtCore import QEvent
from app.geometry_utils import GeometryUtils
import math

class Viewport(QOpenGLWidget):

    def __init__(self, main_window=None):
        super().__init__()

        self.main_window = main_window

        # ---------------------------------
        # Webcam
        # ---------------------------------

        self.webcam_frame = None
        self.webcam_texture = None

        # ---------------------------------
        # Camera
        # ---------------------------------

        self.camera = Camera()

        # ---------------------------------
        # Scene
        # ---------------------------------

        self.scene_objects = []

        # ---------------------------------
        # Cursor
        # ---------------------------------

        self.cursor_x = 0.0
        self.cursor_y = 0.0

        # ---------------------------------
        # Viewport Focus
        # ---------------------------------

        self.setFocusPolicy(Qt.StrongFocus)

        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.mouse_x = 0
        self.mouse_y = 0

        self.right_mouse = False
        self.mouse_pressed = False

        # ---------------------------------
        # Selection
        # ---------------------------------

        self.selection_manager = SelectionManager(self)

        self.selected_vertex = None
        self.selected_vertices = set()
        self.selected_edge = None
        self.selected_edges = set()
        self.selected_face = None
        self.selected_faces = set()

        # ---------------------------------
        # Edit Mode Selection Modes
        # ---------------------------------

        self.vertex_mode = True
        self.edge_mode = False
        self.face_mode = False

        # ---------------------------------
        # Vertex Dragging
        # ---------------------------------

        self.vertex_dragging = False
        self.vertex_drag_start = None
        self.vertex_original = None

        # ---------------------------------
        # Edge Dragging
        # ---------------------------------

        self.edge_dragging = False

        self.edge_vertex_a = None
        self.edge_vertex_b = None

        # ---------------------------------
        # Face Dragging
        # ---------------------------------

        self.face_dragging = False
        self.face_original_vertices = None

        # ---------------------------------
        # Extrude
        # ---------------------------------

        self.extrude_mode = False
        self.extrude_dragging = False

        self.extrude_face = None

        self.extrude_original = None

        self.extrude_original_vertices = []

        self.extrude_vertex_indices = []

        self.extrude_normal = None

        self.extrude_distance = 0.5

        self.extrude_start_distance = 0.5

        self.extrude_start_mouse_x = 0
        self.extrude_start_mouse_y = 0

        # ---------------------------------
        # Ray Casting
        # ---------------------------------

        self.raycaster = RayCaster()

        # ---------------------------------
        # Object Dragging
        # ---------------------------------

        self.dragging_object = False

        # Tracks whether the current Move Gizmo drag has
        # already been recorded in history.
        self._move_saved = False

        # Tracks whether the current object drag has
        # already been recorded in history.
        self._object_drag_saved = False

        self.drag_start_x = 0
        self.drag_start_y = 0

        self.drag_plane_y = 0.0
        self.drag_offset = None

        # ---------------------------------
        # Move Gizmo
        # ---------------------------------

        self.move_gizmo = MoveGizmo()

        # ---------------------------------
        # Rotate Gizmo
        # ---------------------------------

        self.rotate_gizmo = RotateGizmo()

        # ---------------------------------
        # Scale Gizmo
        # ---------------------------------

        self.scale_gizmo = ScaleGizmo()

        # ---------------------------------
        # Tool Manager
        # ---------------------------------

        self.tool_manager = ToolManager()

        # ---------------------------------
        # Final Focus
        # ---------------------------------

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        print(
            "Viewport Focus:",
            self.hasFocus()
        )
                    
    def initializeGL(self):

        print("OpenGL Initialized")

        glEnable(GL_DEPTH_TEST)

        glDisable(GL_CULL_FACE)

        glFrontFace(GL_CCW)

        glClearColor(
            0.15,
            0.15,
            0.15,
            1.0
        )

        self.webcam_texture = glGenTextures(1)

        glBindTexture(
            GL_TEXTURE_2D,
            self.webcam_texture
        )

        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_MIN_FILTER,
            GL_LINEAR
        )

        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_MAG_FILTER,
            GL_LINEAR
        )

        glBindTexture(
            GL_TEXTURE_2D,
            0
        )

    def resizeGL(self, w, h):

        if h == 0:
            h = 1

        glViewport(
            0,
            0,
            w,
            h
        )

        glMatrixMode(
            GL_PROJECTION
        )

        glLoadIdentity()

        gluPerspective(
            45,
            w / h,
            0.1,
            100.0
        )

        glMatrixMode(
            GL_MODELVIEW
        )

    def draw_scene_object(self, obj):

        obj.bounding_box.update(
            obj.position,
            obj.scale
        )

        glPushMatrix()

        # -----------------------------
        # Apply LOCAL transform
        # -----------------------------

        glTranslatef(
            obj.position[0],
            obj.position[1],
            obj.position[2]
        )

        glRotatef(obj.rotation[0], 1, 0, 0)
        glRotatef(obj.rotation[1], 0, 1, 0)
        glRotatef(obj.rotation[2], 0, 0, 1)

        glScalef(
            obj.scale[0],
            obj.scale[1],
            obj.scale[2]
        )

        # -----------------------------
        # Selected Color
        # -----------------------------

        if obj == self.selected_object:

            glColor3f(1.0, 1.0, 0.0)

        else:

            glColor3f(0.0, 1.0, 0.0)

        # -----------------------------
        # Draw Primitive
        # -----------------------------

        if obj.object_type == "Cube":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh, self.selected_faces)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edges
                    )

                    self.draw_vertices(obj.mesh)

            else:

                self.draw_cube()

        elif obj.object_type == "Sphere":

             if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh, self.selected_faces)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edges
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Plane":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh, self.selected_faces)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edges
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Cylinder":

             if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh, self.selected_faces)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edges
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Cone":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh, self.selected_faces)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edges
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Torus":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh, self.selected_faces)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edges
                    )

                    self.draw_vertices(obj.mesh)

        else:

            self.draw_cube()

        # -----------------------------
        # Draw Children
        # -----------------------------

        for child in obj.children:

            self.draw_scene_object(child)

        glPopMatrix()

    def draw_vertices(self, mesh):

        if mesh is None:
            return

        glPushAttrib(
            GL_ENABLE_BIT
            | GL_POINT_BIT
            | GL_CURRENT_BIT
        )

        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)

        # ---------------------------------
        # Normal Vertices
        # ---------------------------------

        glPointSize(8)

        glColor3f(
            1.0,
            0.3,
            0.0
        )

        glBegin(GL_POINTS)

        for vertex in mesh.vertices:

            glVertex3f(
                vertex[0],
                vertex[1],
                vertex[2]
            )

        glEnd()

        # ---------------------------------
        # Selected Vertices
        # ---------------------------------

        selected_vertices = getattr(
            self,
            "selected_vertices",
            set()
        )

        glPointSize(12)

        glColor3f(
            1.0,
            1.0,
            0.0
        )

        glBegin(GL_POINTS)

        for vertex_index in selected_vertices:

            if (
                vertex_index < 0
                or vertex_index >= len(mesh.vertices)
            ):
                continue

            vertex = mesh.vertices[
                vertex_index
            ]

            glVertex3f(
                vertex[0],
                vertex[1],
                vertex[2]
            )

        glEnd()

        glEnable(GL_TEXTURE_2D)

        glPopAttrib()

    def extrude_selected_face(self):

        if self.selected_object is None:
            return

        mesh = self.selected_object.mesh

        if mesh is None:
            return

        if self.extrude_face is None:
            return

        if self.extrude_face < 0:
            return

        if self.extrude_face >= len(mesh.faces):
            return

        # ---------------------------------
        # Get Original Face
        # ---------------------------------

        original_face = list(
            mesh.faces[self.extrude_face]
        )

        if len(original_face) < 3:
            return

        # ---------------------------------
        # Calculate Face Normal
        # ---------------------------------

        normal = self.get_face_normal(
            mesh,
            self.extrude_face
        )

        normal = np.array(
            normal,
            dtype=np.float32
        )

        normal_length = np.linalg.norm(
            normal
        )

        if normal_length < 1e-6:
            return

        normal /= normal_length

        print(
            "Extrude Normal:",
            normal
        )

        # ---------------------------------
        # Extrusion Distance
        # ---------------------------------

        distance = 0.5

        # ---------------------------------
        # Duplicate Vertices
        #
        # IMPORTANT:
        # The face normal is reversed here
        # because the current viewport
        # extrusion convention uses the
        # opposite direction.
        # ---------------------------------

        new_vertices = []

        for vertex_index in original_face:

            if vertex_index < 0:
                return

            if vertex_index >= len(
                mesh.vertices
            ):
                return

            vertex = np.array(
                mesh.vertices[vertex_index],
                dtype=np.float32
            )

            new_vertex = (
                vertex
                - normal * distance
            )

            mesh.vertices.append([
                float(new_vertex[0]),
                float(new_vertex[1]),
                float(new_vertex[2])
            ])

            new_vertices.append(
                len(mesh.vertices) - 1
            )

        # ---------------------------------
        # Create Side Faces
        # ---------------------------------

        count = len(
            original_face
        )

        for i in range(count):

            a = original_face[i]

            b = original_face[
                (i + 1) % count
            ]

            c = new_vertices[
                (i + 1) % count
            ]

            d = new_vertices[i]

            mesh.faces.append(
                (a, d, c, b)
            )

        # ---------------------------------
        # CREATE EXTRUDED CAP
        # ---------------------------------

        mesh.faces.append(
            tuple(new_vertices)
        )        
            
        # ---------------------------------
        # Rebuild Topology
        # ---------------------------------

        mesh.build_edges()

        # ---------------------------------
        # Keep Extruded Face Selected
        # ---------------------------------

        self.selected_face = len(mesh.faces) - 1
        self.selected_faces = {
            self.selected_face
        }

        mesh.selected_face = self.selected_face

        # ---------------------------------
        # Store Extrusion Normal
        # ---------------------------------

        self.extrude_normal = (
            -normal
        )

        # ---------------------------------
        # Debug
        # ---------------------------------

        print(
            "Extrude Complete"
        )

        print(
            "Vertices :",
            len(mesh.vertices)
        )

        print(
            "Faces    :",
            len(mesh.faces)
        )

        print(
            "Edges    :",
            len(mesh.edges)
        )

    def extrude_selected_faces(self):
        """
        Extrude a connected coplanar face selection as one region. Internal
        edges are not given side walls; only the group's outer boundary is.
        """

        if self.selected_object is None:
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            return False

        selected_faces = set(
            self.selected_faces
        )

        if not selected_faces and self.extrude_face is not None:

            selected_faces = {
                self.extrude_face
            }

        selected_faces = {
            face_index
            for face_index in selected_faces
            if 0 <= face_index < len(mesh.faces)
            and len(mesh.faces[face_index]) >= 3
        }

        if not selected_faces:
            print("EXTRUDE: No valid selected faces")
            return False

        active_face = self.extrude_face

        if active_face not in selected_faces:

            active_face = next(iter(selected_faces))

        normal = np.array(
            self.get_face_normal(
                mesh,
                active_face
            ),
            dtype=np.float32
        )

        normal_length = np.linalg.norm(normal)

        if normal_length < 1e-6:
            print("EXTRUDE: Invalid face normal")
            return False

        normal /= normal_length

        # A region extrusion needs one shared direction. Reject non-coplanar
        # groups rather than generating twisted geometry.
        for face_index in selected_faces:

            face_normal = np.array(
                self.get_face_normal(
                    mesh,
                    face_index
                ),
                dtype=np.float32
            )

            face_normal_length = np.linalg.norm(face_normal)

            if face_normal_length < 1e-6:
                print("EXTRUDE: Invalid face normal")
                return False

            face_normal /= face_normal_length

            if np.dot(normal, face_normal) < 0.999:
                print(
                    "EXTRUDE: Selected faces must be coplanar"
                )
                return False

        # Count each undirected edge. A boundary edge occurs once; an internal
        # region edge occurs twice and must not create a side wall.
        edge_faces = {}
        boundary_edges = []

        for face_index in selected_faces:

            face = mesh.faces[face_index]

            for index, vertex_a in enumerate(face):

                vertex_b = face[
                    (index + 1) % len(face)
                ]

                edge_key = tuple(
                    sorted((vertex_a, vertex_b))
                )

                edge_faces.setdefault(
                    edge_key,
                    []
                ).append(face_index)

        # Every selected face must connect to the rest through an edge.
        # Single-face extrusion is naturally connected.
        connected_faces = {active_face}
        pending_faces = [active_face]

        while pending_faces:

            current_face = pending_faces.pop()

            for face_indices in edge_faces.values():

                if current_face not in face_indices:
                    continue

                for neighboring_face in face_indices:

                    if neighboring_face not in connected_faces:

                        connected_faces.add(
                            neighboring_face
                        )

                        pending_faces.append(
                            neighboring_face
                        )

        if connected_faces != selected_faces:
            print(
                "EXTRUDE: Selected faces must form one connected region"
            )
            return False

        for edge_key, face_indices in edge_faces.items():

            if len(face_indices) != 1:
                continue

            face = mesh.faces[face_indices[0]]

            for index, vertex_a in enumerate(face):

                vertex_b = face[
                    (index + 1) % len(face)
                ]

                if tuple(sorted((vertex_a, vertex_b))) == edge_key:

                    boundary_edges.append(
                        (vertex_a, vertex_b)
                    )

                    break

        vertex_map = {}
        distance = 0.5

        for face_index in selected_faces:

            for vertex_index in mesh.faces[face_index]:

                if vertex_index in vertex_map:
                    continue

                vertex = np.array(
                    mesh.vertices[vertex_index],
                    dtype=np.float32
                )

                new_vertex = vertex - normal * distance

                mesh.vertices.append([
                    float(new_vertex[0]),
                    float(new_vertex[1]),
                    float(new_vertex[2])
                ])

                vertex_map[vertex_index] = (
                    len(mesh.vertices) - 1
                )

        for vertex_a, vertex_b in boundary_edges:

            mesh.faces.append((
                vertex_a,
                vertex_map[vertex_a],
                vertex_map[vertex_b],
                vertex_b
            ))

        cap_indices = []

        for face_index in sorted(selected_faces):

            cap_face = tuple(
                vertex_map[vertex_index]
                for vertex_index in mesh.faces[face_index]
            )

            mesh.faces.append(cap_face)

            cap_indices.append(
                len(mesh.faces) - 1
            )

        mesh.build_edges()

        self.selected_faces = set(cap_indices)
        self.selected_face = cap_indices[-1]
        mesh.selected_face = self.selected_face

        self.extrude_normal = -normal

        print(
            "EXTRUDE COMPLETE | Faces:",
            sorted(selected_faces),
            "| Caps:",
            cap_indices
        )

        return True

    def get_face_normal(self, mesh, face_index):

        if mesh is None:
            return np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32
            )

        if face_index is None:
            return np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32
            )

        if face_index >= len(mesh.faces):
            return np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32
            )

        face = mesh.faces[face_index]

        if len(face) < 3:
            return np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32
            )

        v0 = np.array(
            mesh.vertices[face[0]],
            dtype=np.float32
        )

        v1 = np.array(
            mesh.vertices[face[1]],
            dtype=np.float32
        )

        v2 = np.array(
            mesh.vertices[face[2]],
            dtype=np.float32
        )

        edge1 = v1 - v0
        edge2 = v2 - v0

        normal = np.cross(
            edge1,
            edge2
        )

        length = np.linalg.norm(normal)

        if length < 1e-6:
            return np.array(
                [0.0, 0.0, 1.0],
                dtype=np.float32
            )

        normal /= length

        return normal

    def paintGL(self):
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        self.camera.apply()

        # -------------------------
        # World
        # -------------------------
        self.draw_grid()
        self.draw_axes()

        # -------------------------
        # Objects
        # -------------------------
        for obj in self.scene_objects:

            if obj.parent is None:

                print(
                    obj.name,
                    " Parent = ",
                    obj.parent.name if obj.parent else "None"
                )

                self.draw_scene_object(obj)

        # -------------------------
        # Cursor
        # -------------------------
        self.draw_cursor()

        # -------------------------
        # Gizmos
        # -------------------------
        tool = self.tool_manager.get_tool()

        print("Current Tool =", tool)

        if tool == ToolManager.MOVE:

            print("DRAW MOVE")

            self.move_gizmo.draw(self.camera)

        elif tool == ToolManager.ROTATE:

            self.rotate_gizmo.draw()
        
        elif tool == ToolManager.SCALE:

            self.scale_gizmo.draw(self.camera)

        # -------------------------
        # Webcam Overlay
        # -------------------------
        self.upload_webcam_texture()
        self.draw_webcam_texture()

    def draw_cube(self):

        glBegin(GL_QUADS)

        # Front
        glVertex3f(-0.5,-0.5,0.5)
        glVertex3f(0.5,-0.5,0.5)
        glVertex3f(0.5,0.5,0.5)
        glVertex3f(-0.5,0.5,0.5)

        # Back
        glVertex3f(0.5,-0.5,-0.5)
        glVertex3f(-0.5,-0.5,-0.5)
        glVertex3f(-0.5,0.5,-0.5)
        glVertex3f(0.5,0.5,-0.5)

        # Left
        glVertex3f(-0.5,-0.5,-0.5)
        glVertex3f(-0.5,-0.5,0.5)
        glVertex3f(-0.5,0.5,0.5)
        glVertex3f(-0.5,0.5,-0.5)

        # Right
        glVertex3f(0.5,-0.5,0.5)
        glVertex3f(0.5,-0.5,-0.5)
        glVertex3f(0.5,0.5,-0.5)
        glVertex3f(0.5,0.5,0.5)

        # Top
        glVertex3f(-0.5,0.5,0.5)
        glVertex3f(0.5,0.5,0.5)
        glVertex3f(0.5,0.5,-0.5)
        glVertex3f(-0.5,0.5,-0.5)

        # Bottom
        glVertex3f(-0.5,-0.5,-0.5)
        glVertex3f(0.5,-0.5,-0.5)
        glVertex3f(0.5,-0.5,0.5)
        glVertex3f(-0.5,-0.5,0.5)

        glEnd()

    def draw_grid(self):

        glColor3f(
            0.35,
            0.35,
            0.35
        )

        glDisable(GL_DEPTH_TEST)

        glBegin(GL_LINES)

        size = 20
        step = 1

        for i in range(-size, size + 1, step):

            # Lines along Z

            glVertex3f(
                i,
                0,
                -size
            )

            glVertex3f(
                i,
                0,
                size
            )

            # Lines along X

            glVertex3f(
                -size,
                0,
                i
            )

            glVertex3f(
                size,
                0,
                i
            )

        glEnd()

        glEnable(GL_DEPTH_TEST)

    def draw_axes(self):

        glLineWidth(3)

        glBegin(GL_LINES)

        # X Axis (Red)

        glColor3f(1, 0, 0)

        glVertex3f(0, 0, 0)
        glVertex3f(3, 0, 0)

        # Y Axis (Green)

        glColor3f(0, 1, 0)

        glVertex3f(0, 0, 0)
        glVertex3f(0, 3, 0)

        # Z Axis (Blue)

        glColor3f(0, 0, 1)

        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 3)

        glEnd()

        glLineWidth(1)

    def draw_cursor(self):

        glLoadIdentity()

        self.camera.apply()

        glTranslatef(

            self.cursor_x,

            self.cursor_y,

            0.0

        )

        glColor3f(
            1.0,
            0.0,
            0.0
        )

        glBegin(GL_QUADS)

        glVertex3f(-0.05, -0.05, 0.0)
        glVertex3f(0.05, -0.05, 0.0)
        glVertex3f(0.05, 0.05, 0.0)
        glVertex3f(-0.05, 0.05, 0.0)

        glEnd()

    def update_cursor(self, x, y):

        smooth = 0.25

        self.cursor_x += (
            x - self.cursor_x
        ) * smooth

        self.cursor_y += (
            y - self.cursor_y
        ) * smooth

        self.update()

    def update_scene(self, scene_objects):

        self.scene_objects = scene_objects

        self.update()

    def set_selected_object(self, obj):

        print("================================")
        print("OBJECT SELECTED:", obj)

        self.selection_manager.select(obj)

        print("Move Target   :", self.move_gizmo.target)
        print("Rotate Target :", self.rotate_gizmo.target)
        print("Scale Target  :", self.scale_gizmo.target)
        print("================================")
        
    @property
    def selected_object(self):

        return self.selection_manager.get_selected()

    def select_object_at_cursor(self):

        closest = None

        for obj in self.scene_objects:

            dx = obj.position[0] - self.cursor_x
            dy = obj.position[1] - self.cursor_y

            distance = (
                dx * dx +
                dy * dy
            ) ** 0.5

            if distance < 0.5:

                closest = obj
                break

        if closest:

            self.selection_manager.select(closest)

            print(
                "SELECTED:",
                closest.name
            )

            self.update()
        else:

            self.selection_manager.deselect()

            print("DESELECTED")

            self.update()
            
    def update_webcam_frame(self, frame):

        self.webcam_frame = frame

        self.update()

    def upload_webcam_texture(self):

        if self.webcam_frame is None:
            return

        image = cv2.cvtColor(
            self.webcam_frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, _ = image.shape

        glBindTexture(
            GL_TEXTURE_2D,
            self.webcam_texture
        )

        glTexImage2D(

            GL_TEXTURE_2D,

            0,

            GL_RGB,

            w,

            h,

            0,

            GL_RGB,

            GL_UNSIGNED_BYTE,

            image

        )

        glBindTexture(
            GL_TEXTURE_2D,
            0
        )

    def draw_webcam_texture(self):

        print("MODELVIEW STACK:", glGetIntegerv(GL_MODELVIEW_STACK_DEPTH))
        print("PROJECTION STACK:", glGetIntegerv(GL_PROJECTION_STACK_DEPTH))
        if self.webcam_texture is None:
            return

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width(), self.height(), 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)

        glEnable(GL_TEXTURE_2D)

        glBindTexture(
            GL_TEXTURE_2D,
            self.webcam_texture
        )

        x = self.width() - 260
        y = 20

        w = 240
        h = 180

        glColor3f(1, 1, 1)

        glBegin(GL_QUADS)

        glTexCoord2f(0, 0)
        glVertex2f(x, y)

        glTexCoord2f(1, 0)
        glVertex2f(x + w, y)

        glTexCoord2f(1, 1)
        glVertex2f(x + w, y + h)

        glTexCoord2f(0, 1)
        glVertex2f(x, y + h)

        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)

        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        # Restore MODELVIEW matrix
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        # Restore PROJECTION matrix
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        # IMPORTANT
        glMatrixMode(GL_MODELVIEW)

    def wheelEvent(self, event):

        delta = event.angleDelta().y()

        if delta > 0:

            self.camera.distance -= 0.3

        else:

            self.camera.distance += 0.3

        if self.camera.distance < 2:

            self.camera.distance = 2

        if self.camera.distance > 20:

            self.camera.distance = 20

        self.update()

    def mousePressEvent(self, event):   

        self.setFocus()

        self.mouse_x = event.position().x()
        self.mouse_y = event.position().y()

        if event.button() == Qt.LeftButton:

            ray = RayBuilder.build_ray(
                self.mouse_x,
                self.mouse_y,
                self,
                self.camera
            )

            tool = self.tool_manager.get_tool()

            # -------------------------------------------------
            # EDIT MODE
            # -------------------------------------------------

            if self.main_window.mode_manager.get_mode() == "EDIT":

                obj = self.selected_object

                if obj is not None:

                    # =================================================
                    # VERTEX MODE
                    # =================================================

                    if self.vertex_mode:

                        vertex = self.pick_vertex(
                            obj,
                            ray
                        )

                        shift_pressed = bool(
                            event.modifiers() & Qt.ShiftModifier
                        )

                        print(
                            "Selected Vertex:",
                            vertex
                        )

                        # ---------------------------------
                        # Vertex Multi-Selection
                        # ---------------------------------

                        if vertex is not None:

                            if shift_pressed:

                                # Shift + click toggles the vertex.

                                if vertex in self.selected_vertices:

                                    self.selected_vertices.remove(
                                        vertex
                                    )

                                    print(
                                        "Vertex Removed:",
                                        vertex
                                    )

                                else:

                                    self.selected_vertices.add(
                                        vertex
                                    )

                                    print(
                                        "Vertex Added:",
                                        vertex
                                    )

                            else:

                                # Clicking an already-selected vertex keeps
                                # the current multi-selection for dragging.

                                if vertex not in self.selected_vertices:

                                    self.selected_vertices = {
                                        vertex
                                    }

                                    print(
                                        "Vertex Selection Reset:",
                                        vertex
                                    )

                                else:

                                    print(
                                        "Vertex Already Selected - Keeping Group"
                                    )

                            # Keep the clicked vertex as the active vertex
                            # for the existing single-vertex systems.

                            self.selected_vertex = vertex

                            # ---------------------------------
                            # Disable Other Element Selection
                            # ---------------------------------

                            self.selected_edge = None
                            self.selected_edges.clear()
                            self.selected_face = None
                            self.selected_faces.clear()

                            # ---------------------------------
                            # Dragging
                            # ---------------------------------

                            self.dragging_object = False

                            # Only start a vertex drag when the clicked
                            # vertex is still selected.

                            if vertex in self.selected_vertices:

                                self.vertex_dragging = True

                                self.edge_dragging = False
                                self.face_dragging = False

                                self.last_mouse_x = event.x()
                                self.last_mouse_y = event.y()

                                self.vertex_original = np.array(
                                    obj.mesh.vertices[vertex],
                                    dtype=np.float32
                                )

                            else:

                                self.vertex_dragging = False

                        else:

                            # Clicking empty space keeps the current
                            # selection for now.

                            self.vertex_dragging = False
                            
                    # =================================================
                    # EDGE MODE
                    # =================================================

                    elif self.edge_mode:

                        edge = self.pick_edge(
                            obj,
                            ray
                        )

                        shift_pressed = (
                            event.modifiers()
                            & Qt.KeyboardModifier.ShiftModifier
                        )

                        if edge is not None:

                            self.selected_faces.clear()
                            self.selected_face = None

                            if shift_pressed:

                                if edge in self.selected_edges:

                                    self.selected_edges.remove(
                                        edge
                                    )

                                    print(
                                        "Edge Removed:",
                                        edge
                                    )

                                else:

                                    self.selected_edges.add(
                                        edge
                                    )

                                    print(
                                        "Edge Added:",
                                        edge
                                    )

                            else:

                                if edge not in self.selected_edges:

                                    self.selected_edges = {
                                        edge
                                    }

                                    print(
                                        "Edge Selection Reset:",
                                        edge
                                    )

                                else:

                                    print(
                                        "Edge Already Selected - Keeping Group"
                                    )

                            if shift_pressed:

                                # Shift-click changes the selection only.
                                # It must not begin a drag or create an undo
                                # snapshot.
                                self.selected_edge = (
                                    next(
                                        iter(self.selected_edges),
                                        None
                                    )
                                )

                                self.edge_dragging = False
                                self.edge_vertex_a = None
                                self.edge_vertex_b = None

                            else:

                                # A normal click on any selected edge starts
                                # a drag for the complete selected group.
                                self.selected_edge = edge

                                self.dragging_object = False

                                self.edge_dragging = True
                                self.vertex_dragging = False
                                self.face_dragging = False

                                self.selected_vertex = None
                                self.selected_face = None

                                edge_vertices = (
                                    obj.mesh.edges[edge]
                                )

                                self.edge_vertex_a = (
                                    edge_vertices[0]
                                )

                                self.edge_vertex_b = (
                                    edge_vertices[1]
                                )

                                # -----------------------------------------
                                # Begin ESC cancellation snapshot
                                # -----------------------------------------

                                self._begin_cancel_snapshot()

                                # -----------------------------------------
                                # Save undo state
                                # -----------------------------------------

                                if self.history_manager is not None:

                                    self.history_manager.save_state(
                                        self.selected_object
                                    )

                                self.last_mouse_x = event.x()
                                self.last_mouse_y = event.y()

                            print(
                                "Selected Edge:",
                                self.selected_edge
                            )

                        else:

                            self.selected_edge = None
                            self.edge_dragging = False

                    # =================================================
                    # FACE MODE
                    # =================================================

                    elif self.face_mode:

                        face = self.pick_face(
                            obj,
                            ray
                        )

                        if face is not None:

                            # Face mode has its own exclusive selection set.
                            self.selected_vertices.clear()
                            self.selected_edges.clear()
                            self.selected_edge = None

                            shift_pressed = bool(
                                event.modifiers()
                                & Qt.KeyboardModifier.ShiftModifier
                            )

                            if shift_pressed:

                                if face in self.selected_faces:

                                    self.selected_faces.remove(
                                        face
                                    )

                                    print(
                                        "Face Removed:",
                                        face
                                    )

                                else:

                                    self.selected_faces.add(
                                        face
                                    )

                                    print(
                                        "Face Added:",
                                        face
                                    )

                                # Shift-click only changes the selection.
                                self.selected_face = next(
                                    iter(self.selected_faces),
                                    None
                                )

                                self.face_dragging = False

                            else:

                                if face not in self.selected_faces:

                                    self.selected_faces = {
                                        face
                                    }

                                    print(
                                        "Face Selection Reset:",
                                        face
                                    )

                                else:

                                    print(
                                        "Face Already Selected - Keeping Group"
                                    )

                                # A normal click starts a drag for the
                                # complete selected face group.
                                self.selected_face = face

                                self.dragging_object = False

                                self.face_dragging = True
                                self.vertex_dragging = False
                                self.edge_dragging = False

                                self.selected_vertex = None
                                self.selected_edge = None

                                if self.history_manager is not None:

                                    self.history_manager.save_state(
                                        self.selected_object
                                    )

                                self.last_mouse_x = event.x()
                                self.last_mouse_y = event.y()

                            obj.mesh.selected_face = (
                                self.selected_face
                            )

                            print(
                                "Selected Faces:",
                                self.selected_faces
                            )

                        else:

                            self.selected_face = None
                            self.selected_faces.clear()
                            obj.mesh.selected_face = None
                            self.face_dragging = False

                    self.update()

                    return

            # -------------------------------------------------
            # OBJECT MODE
            # -------------------------------------------------

            obj = self.pick_object()

            print(
                "Picked Object:",
                obj
            )

            # The object must be selected BEFORE any history state
            # is saved. Otherwise Undo may record None or a stale object.
            if obj is not None:

                self.set_selected_object(obj)

            # ---------------- MOVE ----------------

            if tool == ToolManager.MOVE:

                axis = self.move_gizmo.pick_axis(
                    ray
                )

                if axis is not None:

                    print(
                        "Move Axis:",
                        axis
                    )

                    self.move_gizmo.selected_axis = axis

                    if self.selected_object is not None:

                        self.history_manager.save_state(
                            self.selected_object
                        )

                    self.last_mouse_x = event.x()
                    self.last_mouse_y = event.y()

                    self._move_saved = True

                    self.update()

                    return

            # ---------------- ROTATE ----------------

            elif tool == ToolManager.ROTATE:

                rotate_axis = (
                    self.rotate_gizmo.pick_axis(
                        ray
                    )
                )

                if rotate_axis is not None:

                    print(
                        "Rotate Axis:",
                        rotate_axis
                    )

                    self.rotate_gizmo.selected_axis = (
                        rotate_axis
                    )

                    self.history_manager.save_state(
                        self.selected_object
                    )

                    self.rotate_gizmo.begin_rotation(
                        rotate_axis,
                        ray
                    )

                    self.last_mouse_x = event.x()
                    self.last_mouse_y = event.y()

                    self.update()

                    return

            # ---------------- SCALE ----------------

            elif tool == ToolManager.SCALE:

                scale_axis = (
                    self.scale_gizmo.pick_axis(
                        ray
                    )
                )

                if scale_axis is not None:

                    print(
                        "Scale Axis:",
                        scale_axis
                    )

                    self.scale_gizmo.selected_axis = (
                        scale_axis
                    )

                    self.history_manager.save_state(
                        self.selected_object
                    )

                    self.scale_gizmo.begin_scale(
                        scale_axis,
                        ray
                    )

                    self.last_mouse_x = event.x()
                    self.last_mouse_y = event.y()

                    self.update()

                    return

            # ---------------- OBJECT PICK ----------------

            if obj is not None:

                # obj was selected above before the transform
                # tool branches. Record the state immediately
                # before the normal object drag begins.
                self.set_selected_object(
                    obj
                )

                if self.history_manager is not None:

                    self.history_manager.save_state(
                        self.selected_object
                    )

                self._object_drag_saved = True
                self.dragging_object = True

                if abs(ray.direction[1]) > 1e-6:

                    t = (
                        self.drag_plane_y
                        - ray.origin[1]
                    ) / ray.direction[1]

                    hit = (
                        ray.origin
                        + ray.direction * t
                    )

                    self.drag_offset = (
                        np.array(
                            self.selected_object.position
                        )
                        - hit
                    )

                self.drag_start_x = event.x()
                self.drag_start_y = event.y()

                print(
                    "Selected:",
                    obj.name
                )

            else:

                self.selection_manager.deselect()

            self.update()

            return

        # -------------------------------------------------
        # RIGHT MOUSE
        # -------------------------------------------------

        if event.button() == Qt.RightButton:

            self.right_mouse = True

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

        self.setFocus()

        print(
            "Viewport Focus:",
            self.hasFocus()
        )
            
    def mouseReleaseEvent(self, event):

        # ---------------------------------
        # LEFT MOUSE RELEASE
        # ---------------------------------

        if event.button() == Qt.LeftButton:

            # ---------------------------------
            # Vertex Drag
            # ---------------------------------

            self.vertex_dragging = False

            # ---------------------------------
            # Edge Drag
            # ---------------------------------

            self.edge_dragging = False

            self.edge_vertex_a = None
            self.edge_vertex_b = None

            # ---------------------------------
            # Face Drag
            # ---------------------------------

            self.face_dragging = False

            # ---------------------------------
            # Extrude
            # ---------------------------------

            self.extrude_dragging = False
            self.extrude_mode = False

            print("Extrude Released")

            self.extrude_vertex_indices = []

            self.extrude_original_vertices = []

            self.extrude_normal = None

            self.extrude_face = None

            self.extrude_distance = 0.0

            # ---------------------------------
            # Object Drag
            # ---------------------------------

            self.dragging_object = False

            # ---------------------------------
            # Move Gizmo
            # ---------------------------------

            self.move_gizmo.selected_axis = None

            # ---------------------------------
            # Rotate Gizmo
            # ---------------------------------

            self.rotate_gizmo.selected_axis = None
            self.rotate_gizmo.dragging = False

            self.rotate_gizmo.end_rotation()

            # ---------------------------------
            # Scale Gizmo
            # ---------------------------------

            self.scale_gizmo.selected_axis = None

            self.scale_gizmo.end_scale()

            # ---------------------------------
            # History
            # ---------------------------------

            self._move_saved = False
            self._object_drag_saved = False

        # ---------------------------------
        # RIGHT MOUSE RELEASE
        # ---------------------------------

        elif event.button() == Qt.RightButton:

            self.right_mouse = False

        # ---------------------------------
        # Update Viewport
        # ---------------------------------

        self.update()
        
    def mouseMoveEvent(self, event):

        # ---------------------------------
        # INTERACTIVE EXTRUDE
        # ---------------------------------

        if (
            self.extrude_mode
            and self.extrude_dragging
            and self.selected_object is not None
            and self.main_window.mode_manager.get_mode() == "EDIT"
        ):

            print("EXTRUDE MOUSE MOVE")

            mesh = self.selected_object.mesh

            if mesh is None:
                return

            if self.extrude_normal is None:
                return

            if not self.extrude_vertex_indices:
                return

            if not self.extrude_original_vertices:
                return

            # ---------------------------------
            # Face Normal
            # ---------------------------------

            normal = np.array(
                self.extrude_normal,
                dtype=np.float64
            )

            normal_length = np.linalg.norm(normal)

            if normal_length < 1e-8:
                return

            normal /= normal_length

            print(
                "EXTRUDE DEBUG| Normal:",
                normal
            )

            # ---------------------------------
            # Mouse Movement
            # ---------------------------------

            dx = (
                event.x()
                - self.extrude_start_mouse_x
            )

            dy = (
                self.extrude_start_mouse_y
                - event.y()
            )

            # ---------------------------------
            # Camera Screen Basis
            # ---------------------------------

            camera_right = np.array(
                self.camera.get_right(),
                dtype=np.float64
            )

            camera_up = np.array(
                self.camera.get_up(),
                dtype=np.float64
            )

            right_length = np.linalg.norm(
                camera_right
            )

            up_length = np.linalg.norm(
                camera_up
            )

            if right_length < 1e-8:
                return

            if up_length < 1e-8:
                return

            camera_right /= right_length
            camera_up /= up_length

            print(
                "CAMERA DEBUG | Right:",
                camera_right,
                "| Up:",
                camera_up
            )
            # ---------------------------------
            # Project Face Normal Onto Screen
            # ---------------------------------

            normal_screen_x = np.dot(
                normal,
                camera_right
            )

            normal_screen_y = np.dot(
                normal,
                camera_up
            )

            screen_length = math.sqrt(
                normal_screen_x ** 2
                + normal_screen_y ** 2
            )

            print(
                "SCREEN NORMAL DEBUG | X:",
                normal_screen_x,
                " | Y:",
                normal_screen_y,
                " | Length:",
                screen_length
            )

            # ---------------------------------
            # Calculate Mouse Movement
            # Along Projected Normal
            # ---------------------------------

            if screen_length > 1e-8:

                screen_x = (
                    normal_screen_x
                    / screen_length
                )

                screen_y = (
                    normal_screen_y
                    / screen_length
                )

                mouse_delta = (
                    dx * screen_x
                    + dy * screen_y
                )

            else:

                # Face normal points almost directly
                # toward/away from the camera.
                #
                # In this case there is almost no
                # visible screen direction for the
                # normal, so use vertical mouse movement
                # as a fallback.

                mouse_delta = dy

            # ---------------------------------
            # Preserve Existing Face Directions
            # ---------------------------------

            # Bottom face has the opposite normal
            # relative to the top face.

            if normal[1] < -0.5:

                mouse_delta = -mouse_delta

            # Left face has the opposite normal
            # relative to the right face.

            elif normal[0] < -0.5:

                mouse_delta = -mouse_delta

            # ---------------------------------
            # Extrusion Distance
            # ---------------------------------

            sensitivity = 0.01

            self.extrude_distance = (
                self.extrude_start_distance
                + mouse_delta * sensitivity
            )

            # ---------------------------------
            # Extrusion Offset
            # ---------------------------------

            extrusion_offset = (
                normal
                * self.extrude_distance
            )

            # ---------------------------------
            # Move Extruded Vertices
            # ---------------------------------

            for i, vertex_index in enumerate(
                self.extrude_vertex_indices
            ):

                if vertex_index < 0:
                    continue

                if vertex_index >= len(
                    mesh.vertices
                ):
                    continue

                if i >= len(
                    self.extrude_original_vertices
                ):
                    continue

                original_vertex = np.array(
                    self.extrude_original_vertices[i],
                    dtype=np.float64
                )

                new_vertex = (
                    original_vertex
                    + extrusion_offset
                )

                mesh.vertices[
                    vertex_index
                ] = [
                    float(new_vertex[0]),
                    float(new_vertex[1]),
                    float(new_vertex[2])
                ]

                print("EXTRUDE VERTEX:",
                    vertex_index,
                    mesh.vertices[vertex_index]

                )

            # ---------------------------------
            # Rebuild Topology
            # ---------------------------------

            try:
                mesh.build_edges()
            except Exception as e:
                print("EXTRUDE EDGE BUILD ERROR:", e)
                return

            # ---------------------------------
            # Update Bounding Box
            # ---------------------------------

            if hasattr(
                self.selected_object,
                "bounding_box"
            ):

                self.selected_object.bounding_box.update(
                    self.selected_object.position,
                    self.selected_object.scale
                )

            # ---------------------------------
            # Redraw
            # ---------------------------------

            self.update()

            return

        # ---------------------------------
        # VERTEX DRAG
        # ---------------------------------

        if (
            self.vertex_dragging
            and self.selected_vertex is not None
            and self.selected_object is not None
            and self.main_window.mode_manager.get_mode() == "EDIT"
        ):

            mesh = self.selected_object.mesh

            if mesh is None:
                return

            if self.selected_vertex < 0:
                return

            if self.selected_vertex >= len(mesh.vertices):
                return

            # ---------------------------------
            # Mouse Movement
            # ---------------------------------

            dx = (
                event.x()
                - self.last_mouse_x
            )

            dy = (
                event.y()
                - self.last_mouse_y
            )

            sensitivity = 0.01

            move_x = dx * sensitivity
            move_y = -dy * sensitivity

            # ---------------------------------
            # Move All Selected Vertices
            # ---------------------------------

            for vertex_index in self.selected_vertices:

                if vertex_index < 0:
                    continue

                if vertex_index >= len(mesh.vertices):
                    continue

                mesh.vertices[vertex_index][0] += move_x
                mesh.vertices[vertex_index][1] += move_y

            # ---------------------------------
            # Update Mouse Position
            # ---------------------------------

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            # ---------------------------------
            # Rebuild Edges
            # ---------------------------------

            try:
                mesh.build_edges()
            except Exception as e:
                print(
                    "VERTEX EDGE BUILD ERROR:",
                    e
                )
                return

            # ---------------------------------
            # Redraw
            # ---------------------------------

            self.update()

            return

        # ---------------------------------
        # EDGE DRAG
        # ---------------------------------

        if (
            self.edge_dragging
            and self.selected_object is not None
            and self.main_window.mode_manager.get_mode() == "EDIT"
        ):

            mesh = self.selected_object.mesh

            if mesh is None:
                return

            selected_edges = set(
                self.selected_edges
            )

            # Keep normal single-edge dragging compatible.
            if not selected_edges:

                if self.selected_edge is None:
                    return

                selected_edges = {
                    self.selected_edge
                }

            dx = (
                event.x()
                - self.last_mouse_x
            )

            dy = (
                event.y()
                - self.last_mouse_y
            )

            sensitivity = 0.01

            move_x = (
                dx * sensitivity
            )

            move_y = (
                -dy * sensitivity
            )

            # Collect vertices once, even when selected
            # edges share a vertex.
            vertices_to_move = set()

            for edge_index in selected_edges:

                if edge_index < 0:
                    continue

                if edge_index >= len(
                    mesh.edges
                ):
                    continue

                edge = mesh.edges[
                    edge_index
                ]

                if len(edge) != 2:
                    continue

                vertex_a = edge[0]
                vertex_b = edge[1]

                if (
                    vertex_a >= 0
                    and vertex_a < len(mesh.vertices)
                ):

                    vertices_to_move.add(
                        vertex_a
                    )

                if (
                    vertex_b >= 0
                    and vertex_b < len(mesh.vertices)
                ):

                    vertices_to_move.add(
                        vertex_b
                    )

            for vertex_index in vertices_to_move:

                vertex = mesh.vertices[
                    vertex_index
                ]

                vertex[0] += move_x
                vertex[1] += move_y

                mesh.vertices[
                    vertex_index
                ] = vertex

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # FACE DRAG
        # ---------------------------------

        if (
            self.face_dragging
            and self.selected_object is not None
            and self.main_window.mode_manager.get_mode() == "EDIT"
        ):

            mesh = self.selected_object.mesh

            if mesh is None:
                return

            selected_faces = set(
                self.selected_faces
            )

            if not selected_faces and self.selected_face is not None:

                selected_faces = {
                    self.selected_face
                }

            if not selected_faces:
                return

            dx = (
                event.x()
                - self.last_mouse_x
            )

            dy = (
                event.y()
                - self.last_mouse_y
            )

            sensitivity = 0.01

            # Move shared vertices just once when selected faces touch.
            vertices_to_move = set()

            for face_index in selected_faces:

                if (
                    face_index < 0
                    or face_index >= len(mesh.faces)
                ):
                    continue

                for vertex_index in mesh.faces[face_index]:

                    if (
                        vertex_index >= 0
                        and vertex_index < len(mesh.vertices)
                    ):

                        vertices_to_move.add(
                            vertex_index
                        )

            for vertex_index in vertices_to_move:

                vertex = mesh.vertices[
                    vertex_index
                ]

                vertex[0] += (
                    dx * sensitivity
                )

                vertex[1] -= (
                    dy * sensitivity
                )

                mesh.vertices[
                    vertex_index
                ] = vertex

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # SCALE GIZMO
        # ---------------------------------

        if (
            event.buttons() & Qt.LeftButton
            and self.scale_gizmo.dragging
            and self.scale_gizmo.selected_axis is not None
            and self.selected_object is not None
        ):

            self.scale_gizmo.scale(
                event.x(),
                event.y(),
                self.last_mouse_x,
                self.last_mouse_y
            )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # ROTATE GIZMO
        # ---------------------------------

        if (
            event.buttons() & Qt.LeftButton
            and self.rotate_gizmo.dragging
            and self.rotate_gizmo.selected_axis is not None
            and self.selected_object is not None
        ):

            ray = RayBuilder.build_ray(
                event.x(),
                event.y(),
                self,
                self.camera
            )

            self.rotate_gizmo.rotate(
                ray
            )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # MOVE GIZMO
        # ---------------------------------

        if (
            event.buttons() & Qt.LeftButton
            and self.move_gizmo.selected_axis is not None
            and self.selected_object is not None
        ):

            if not self._move_saved:

                if self.history_manager is not None:
                    self.history_manager.save_state(
                        self.selected_object
                    )

                self._move_saved = True

            dx = (
                event.x()
                - self.last_mouse_x
            )

            dy = (
                event.y()
                - self.last_mouse_y
            )

            speed = 0.003

            if (
                self.move_gizmo.selected_axis
                == "X"
            ):

                self.selected_object.translate(
                    dx * speed,
                    0.0,
                    0.0
                )

            elif (
                self.move_gizmo.selected_axis
                == "Y"
            ):

                self.selected_object.translate(
                    0.0,
                    -dy * speed,
                    0.0
                )

            elif (
                self.move_gizmo.selected_axis
                == "Z"
            ):

                self.selected_object.translate(
                    0.0,
                    0.0,
                    dx * speed
                )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # OBJECT DRAG
        # ---------------------------------

        if (
            self.dragging_object
            and self.selected_object
        ):

            ray = RayBuilder.build_ray(
                event.x(),
                event.y(),
                self,
                self.camera
            )

            if abs(
                ray.direction[1]
            ) < 1e-6:

                return

            t = (
                self.drag_plane_y
                - ray.origin[1]
            ) / ray.direction[1]

            hit = (
                ray.origin
                + ray.direction * t
            )

            new_position = (
                hit
                + self.drag_offset
            )

            self.selected_object.position[0] = float(
                new_position[0]
            )

            self.selected_object.position[2] = float(
                new_position[2]
            )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # CAMERA ROTATION
        # ---------------------------------

        if event.buttons() & Qt.RightButton:

            dx = (
                event.x()
                - self.last_mouse_x
            )

            dy = (
                event.y()
                - self.last_mouse_y
            )

            self.camera.yaw -= (
                dx * 0.5
            )

            self.camera.pitch += (
                dy * 0.5
            )

            self.camera.pitch = max(
                -89,
                min(
                    89,
                    self.camera.pitch
                )
            )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()
            
    # ---------------------------------
    # EDIT MODE DELETION
    # ---------------------------------

    def _cleanup_mesh_after_deletion(self, mesh):
        """
        Remove unused vertices, repair face indices, remove degenerate
        faces, and rebuild the derived edge list.

        Faces are the authoritative topology in this mesh implementation.
        Edges are derived from faces by Mesh.build_edges().
        """

        if mesh is None:
            return

        valid_faces = []

        for face in mesh.faces:

            if face is None:
                continue

            face = tuple(
                int(index)
                for index in face
            )

            # A polygon must contain at least three vertices.
            if len(face) < 3:
                continue

            # Remove repeated consecutive/final indices.
            cleaned_face = []

            for index in face:

                if not cleaned_face or index != cleaned_face[-1]:
                    cleaned_face.append(index)

            if (
                len(cleaned_face) > 1
                and cleaned_face[0] == cleaned_face[-1]
            ):
                cleaned_face.pop()

            if len(cleaned_face) < 3:
                continue

            # Reject invalid vertex references.
            if any(
                index < 0
                or index >= len(mesh.vertices)
                for index in cleaned_face
            ):
                continue

            # A polygon with fewer than three unique vertices is invalid.
            if len(set(cleaned_face)) < 3:
                continue

            valid_faces.append(
                tuple(cleaned_face)
            )

        mesh.faces = valid_faces

        # ---------------------------------
        # Find vertices still used by faces
        # ---------------------------------

        used_vertices = set()

        for face in mesh.faces:

            for vertex_index in face:

                used_vertices.add(
                    vertex_index
                )

        # ---------------------------------
        # Rebuild vertex array
        # ---------------------------------

        vertex_remap = {}
        new_vertices = []

        for old_index, vertex in enumerate(mesh.vertices):

            if old_index not in used_vertices:
                continue

            vertex_remap[old_index] = (
                len(new_vertices)
            )

            new_vertices.append(
                [
                    float(vertex[0]),
                    float(vertex[1]),
                    float(vertex[2])
                ]
            )

        # ---------------------------------
        # Remap face indices
        # ---------------------------------

        remapped_faces = []

        for face in mesh.faces:

            remapped_face = []

            valid_face = True

            for old_index in face:

                if old_index not in vertex_remap:

                    valid_face = False
                    break

                remapped_face.append(
                    vertex_remap[old_index]
                )

            if not valid_face:
                continue

            if len(remapped_face) < 3:
                continue

            if len(set(remapped_face)) < 3:
                continue

            remapped_faces.append(
                tuple(remapped_face)
            )

        mesh.vertices = new_vertices
        mesh.faces = remapped_faces

        # ---------------------------------
        # Rebuild derived topology
        # ---------------------------------

        mesh.build_edges()

        # ---------------------------------
        # Clear element selections
        # ---------------------------------

        self.selected_vertex = None
        self.selected_edge = None
        self.selected_edges.clear()
        self.selected_face = None
        self.selected_faces.clear()

        mesh.selected_vertex = None
        mesh.selected_edge = None
        mesh.selected_face = None

    def _delete_selected_vertex(self):
        """
        Delete the selected vertex and every face connected to it.
        """

        if self.selected_object is None:
            print("DELETE VERTEX: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("DELETE VERTEX: Object has no mesh")
            return False

        vertex_index = self.selected_vertex

        if vertex_index is None:
            print("DELETE VERTEX: No selected vertex")
            return False

        if (
            vertex_index < 0
            or vertex_index >= len(mesh.vertices)
        ):
            print("DELETE VERTEX: Invalid vertex")
            self.selected_vertex = None
            mesh.selected_vertex = None
            return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:

            self.history_manager.save_state(
                self.selected_object
            )

        print(
            "DELETE VERTEX:",
            vertex_index
        )

        # ---------------------------------
        # Remove the vertex
        # ---------------------------------

        mesh.vertices.pop(
            vertex_index
        )

        # ---------------------------------
        # Remove faces using the vertex.
        #
        # Remaining indices above the deleted
        # vertex are shifted down by one.
        # ---------------------------------

        new_faces = []

        for face in mesh.faces:

            if vertex_index in face:
                continue

            remapped_face = tuple(
                index - 1
                if index > vertex_index
                else index
                for index in face
            )

            new_faces.append(
                remapped_face
            )

        mesh.faces = new_faces

        # ---------------------------------
        # Repair topology and clear selection
        # ---------------------------------

        self._cleanup_mesh_after_deletion(
            mesh
        )

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.edge_vertex_a = None
        self.edge_vertex_b = None

        self.vertex_original = None
        self.face_original_vertices = None

        print(
            "DELETE VERTEX COMPLETE | "
            "Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True

    def _delete_selected_edge(self):
        """
        Delete the faces connected to one or more selected edges.

        The current mesh representation derives edges from polygon faces,
        so removing an edge entry alone would be temporary and would be
        recreated by Mesh.build_edges(). For this first destructive Edit
        Mode implementation, deleting an edge removes every face incident
        to that edge, then cleans unused vertices and rebuilds topology.
        """

        if self.selected_object is None:
            print("DELETE EDGE: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("DELETE EDGE: Object has no mesh")
            return False

        selected_edge_indices = set(
            self.selected_edges
        )

        # Keep deletion compatible with the earlier single-edge workflow.
        if not selected_edge_indices and self.selected_edge is not None:

            selected_edge_indices = {
                self.selected_edge
            }

        if not selected_edge_indices:
            print("DELETE EDGE: No selected edge")
            return False

        selected_pairs = set()

        for edge_index in selected_edge_indices:

            if (
                edge_index < 0
                or edge_index >= len(mesh.edges)
            ):
                continue

            edge = mesh.edges[
                edge_index
            ]

            if len(edge) != 2:
                continue

            selected_pairs.add(
                frozenset((
                    int(edge[0]),
                    int(edge[1])
                ))
            )

        if not selected_pairs:
            print("DELETE EDGE: No valid selected edges")
            self.selected_edge = None
            self.selected_edges.clear()
            mesh.selected_edge = None
            return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:

            self.history_manager.save_state(
                self.selected_object
            )

        print(
            "DELETE EDGES:",
            sorted(selected_edge_indices)
        )

        # ---------------------------------
        # Remove all incident faces
        # ---------------------------------

        new_faces = []

        removed_faces = 0

        for face in mesh.faces:

            face_vertices = set(face)

            if any(
                edge_vertices.issubset(face_vertices)
                for edge_vertices in selected_pairs
            ):

                removed_faces += 1
                continue

            new_faces.append(
                tuple(face)
            )

        mesh.faces = new_faces

        # ---------------------------------
        # Repair topology and clear selection
        # ---------------------------------

        self._cleanup_mesh_after_deletion(
            mesh
        )

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.edge_vertex_a = None
        self.edge_vertex_b = None

        self.vertex_original = None
        self.face_original_vertices = None

        print(
            "DELETE EDGE COMPLETE | "
            "Removed Faces:",
            removed_faces,
            "| Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True

    def _delete_selected_face(self):
        """
        Delete the selected polygon faces, then remove unused vertices and
        rebuild the derived edge topology.
        """

        if self.selected_object is None:
            print("DELETE FACE: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("DELETE FACE: Object has no mesh")
            return False

        selected_face_indices = set(
            self.selected_faces
        )

        # Keep the original single-face deletion behavior compatible.
        if not selected_face_indices and self.selected_face is not None:

            selected_face_indices = {
                self.selected_face
            }

        if not selected_face_indices:
            print("DELETE FACE: No selected face")
            return False

        valid_face_indices = {
            face_index
            for face_index in selected_face_indices
            if 0 <= face_index < len(mesh.faces)
        }

        if not valid_face_indices:
            print("DELETE FACE: No valid selected faces")
            self.selected_face = None
            self.selected_faces.clear()
            mesh.selected_face = None
            return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:

            self.history_manager.save_state(
                self.selected_object
            )

        print(
            "DELETE FACES:",
            sorted(valid_face_indices)
        )

        # ---------------------------------
        # Remove selected faces together so their original indices remain
        # valid throughout the operation.
        # ---------------------------------

        mesh.faces = [
            tuple(face)
            for face_index, face in enumerate(mesh.faces)
            if face_index not in valid_face_indices
        ]

        # ---------------------------------
        # Repair topology and clear selection
        # ---------------------------------

        self._cleanup_mesh_after_deletion(
            mesh
        )

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.edge_vertex_a = None
        self.edge_vertex_b = None

        self.vertex_original = None
        self.face_original_vertices = None

        print(
            "DELETE FACE COMPLETE | "
            "Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True

    def delete_selected_edit_element(self):
        """
        Delete the currently selected Edit Mode element according to the
        active vertex, edge, or face selection mode.
        """

        if self.main_window.mode_manager.get_mode() != "EDIT":

            print(
                "DELETE EDIT ELEMENT: Requires EDIT mode"
            )

            return False

        deleted = False

        if self.vertex_mode:

            deleted = (
                self._delete_selected_vertex()
            )

        elif self.edge_mode:

            deleted = (
                self._delete_selected_edge()
            )

        elif self.face_mode:

            deleted = (
                self._delete_selected_face()
            )

        else:

            print(
                "DELETE EDIT ELEMENT: "
                "No active selection mode"
            )

            return False

        if deleted:

            # ---------------------------------
            # Reset transient drag state
            # ---------------------------------

            self.extrude_mode = False
            self.extrude_dragging = False
            self.extrude_face = None

            self.extrude_original = None
            self.extrude_original_vertices = []
            self.extrude_vertex_indices = []
            self.extrude_normal = None

            self.extrude_distance = 0.0
            self.extrude_start_distance = 0.0

            self.extrude_start_mouse_x = 0
            self.extrude_start_mouse_y = 0

            self.update()

        return deleted

    def keyPressEvent(self, event):

        print("VIEWPORT KEY:", event.key())

        #--------------------------------
        # ESC - CANCEL CURRENT OPERATION
        # -------------------------------

        if event.key() == Qt.Key_Escape:

            print("ESC - CANCEL CURRENT OPERATION")

            # ---------------------------------
            # CANCEL EXTRUDE
            # ---------------------------------

            if (
                self.extrude_mode
                or self.extrude_dragging
            ):

                print("CANCEL EXTRUDE")

                # ---------------------------------
                # Restore operation snapshot
                # ---------------------------------

                if (
                    self.history_manager is not None
                    and self.history_manager.has_operation()
                ):

                    self.history_manager.cancel_action()

                # ---------------------------------
                # Reset extrusion state
                # ---------------------------------

                self.extrude_mode = False
                self.extrude_dragging = False

                self.extrude_face = None
                self.extrude_original = None

                self.extrude_original_vertices = []
                self.extrude_vertex_indices = []

                self.extrude_normal = None

                self.extrude_distance = 0.0
                self.extrude_start_distance = 0.0

                self.extrude_start_mouse_x = 0
                self.extrude_start_mouse_y = 0

                self.extrude_axis_origin = None
                self.extrude_start_axis_parameter = 0.0

                # ---------------------------------
                # Stop other edit dragging
                # ---------------------------------

                self.vertex_dragging = False
                self.edge_dragging = False
                self.face_dragging = False
                self.dragging_object = False

                self.selected_vertex = None
                self.selected_edge = None

                # ---------------------------------
                # Restore face selection
                # ---------------------------------

                if self.selected_object is not None:

                    mesh = self.selected_object.mesh

                    if mesh is not None:

                        # The cancelled extrusion no longer exists.
                        # Keep the original face selected if it is valid.

                        if (
                            self.selected_face is not None
                            and 0 <= self.selected_face < len(mesh.faces)
                        ):

                            mesh.selected_face = self.selected_face

                        else:

                            mesh.selected_face = None

                print(
                    "Extrude Cancelled"
                )

                self.update()

                return
            #-------------------------------
            # Cancel vertex drag
            #-------------------------------

            if self.vertex_dragging:

                print("CANCEL VERTEX DRAG")

                if (
                    self.selected_object is not None
                    and self.vertex_original is not None
                    and self.selected_object is not None
                ):

                    mesh = self.selected_object.mesh

                    if (
                        mesh is not None
                        and 0 <= self.selected_vertex < len(mesh.vertices)
                    ):
                        original = self.vertex_original

                        mesh.vertices[
                            self.selected_vertex
                        ] = [
                            float(original[0]),
                            float(original[1]),
                            float(original[2])
                        ]

                        mesh.build_edges()

                self.vertex_dragging = False
                self.vertex_drag_start = None
                self.vertex_original = None

                self.update()

                return

            #-------------------------------
            # Cancel face drag
            #-------------------------------

            if self.face_dragging:

                print("CANCEL FACE DRAG")

                if(
                    self.selected_object is not None
                    and self.face_original_vertices is not None
                    and self.selected_face is not None
                ):

                    mesh = self.selected_object.mesh

                    if mesh is not None:

                        face = mesh.faces[self.selected_face]

                        for i, vertex_index in enumerate(face):

                            if i >= len(
                                self.face_original_vertices
                            ):

                                continue

                            if (
                                vertex_index >= 0
                                and vertex_index < len(mesh.vertices)
                            ):

                                original = (
                                    self.face_original_vertices[i]
                                )

                                mesh.vertices[
                                    vertex_index
                                ] = [
                                    float(original[0]),
                                    float(original[1]),
                                    float(original[2])
                                ]

                        mesh.build_edges()

                self.face_dragging = False
                self.face_original_vertices = None

                self.update()

                return

            #------------------------------
            # Cancel edge drag
            #------------------------------

            if self.edge_dragging:

                print("CANCEL EDGE DRAG")

                self.edge_dragging = False

                self.edge_vertex_a = None
                self.edge_vertex_b = None

                self.update()

                return

            #------------------------------
            # Cancel object drag
            #------------------------------

            if self.dragging_object:

                print("CANCEL OBJECT DRAG")

                self.dragging_object = False

                self.drag_start_x = 0
                self.drag_start_y = 0

                self.drag_offset = None

                self.update()

                return

            #------------------------------
            # Cancel move gizmo
            #------------------------------

            if (
                self.move_gizmo.selected_axis is not None
            ):

                print("CANCEL MOVE GIZMO")

                self.move_gizmo.selected_axis = None

                self.update()

                return

            #------------------------------
            # Cancel rotate gizmo
            #------------------------------

            if (
                self.rotate_gizmo.selected_axis is not None
                or self.rotate_gizmo.dragging
            ):

                print("CANCEL ROTATE GIZMO")

                self.rotate_gizmo.selected_axis = None
                self.rotate_gizmo.dragging = False

                self.rotate_gizmo.end_rotation()

                self.update()

                return

            #------------------------------
            # Cancel Scale gizmo
            #------------------------------

            if (
                self.scale_gizmo.selected_axis is not None
            ):

                print("CANCEL SCALE GIZMO")

                self.scale_gizmo.selected_axis = None

                self.scale_gizmo.end_scale()

                self.update()

                return

            #------------------------------
            # Nothing active
            #------------------------------

            print("ESC - NOTHING TO CANCEL")

            self.update()

            return
            
        # ---------------------------------
        # CTRL + Z
        # ---------------------------------
        
        if (
            event.modifiers() & Qt.ControlModifier
            and event.key() == Qt.Key_Z
        ):

            print("UNDO")

            self.history_manager.undo()

            self.update()

            return

        # ---------------------------------
        # CTRL + Y
        # ---------------------------------
        if (
            event.modifiers() & Qt.ControlModifier
            and event.key() == Qt.Key_Y
        ):

            print("REDO")

            self.history_manager.redo()

            self.update()

            return

        # ---------------------------------
        # OBJECT / EDIT MODE
        # ---------------------------------
        if event.key() == Qt.Key_Tab:

            self.main_window.mode_manager.toggle()

            print(
                "MODE:",
                self.main_window.mode_manager.get_mode()
            )

            self.update()

            return

        # ---------------------------------
        # DELETE EDIT ELEMENT
        # ---------------------------------

        if (
            event.key() == Qt.Key_X
            or event.key() == Qt.Key_Delete
        ):

            print(
                "DELETE EDIT ELEMENT"
            )

            # Only consume Delete/X here in Edit Mode.
            # Object Mode Delete continues to be handled by main.py.
            if (
                self.main_window.mode_manager.get_mode()
                == "EDIT"
            ):

                self.delete_selected_edit_element()

                return

        # ---------------------------------
        # VERTEX MODE
        # ---------------------------------
        if event.key() == Qt.Key_1:

            self.vertex_mode = True
            self.edge_mode = False
            self.face_mode = False

            print("VERTEX MODE")

            self.update()

            return

        # ---------------------------------
        # EDGE MODE
        # ---------------------------------
        elif event.key() == Qt.Key_2:

            self.vertex_mode = False
            self.edge_mode = True
            self.face_mode = False

            print("EDGE MODE")

            self.update()

            return

        # ---------------------------------
        # FACE MODE
        # ---------------------------------
        elif event.key() == Qt.Key_3:

            self.vertex_mode = False
            self.edge_mode = False
            self.face_mode = True

            print("FACE MODE")

            self.update()

            return

        # ---------------------------------
        # MOVE
        # ---------------------------------
        elif event.key() == Qt.Key_G:

            print("MOVE")

            self.tool_manager.set_tool(
                ToolManager.MOVE
            )

            self.update()

            return

        # ---------------------------------
        # ROTATE
        # ---------------------------------
        elif event.key() == Qt.Key_R:

            print("ROTATE")

            self.tool_manager.set_tool(
                ToolManager.ROTATE
            )

            self.update()

            return

        # ---------------------------------
        # SCALE
        # ---------------------------------
        elif event.key() == Qt.Key_S:

            print("SCALE")

            self.tool_manager.set_tool(
                ToolManager.SCALE
            )

            self.update()

            return

        # ---------------------------------
        # EXTRUDE
        # ---------------------------------

        elif event.key() == Qt.Key_E:

            print("EXTRUDE")

            # ---------------------------------
            # Edit Mode Check
            # ---------------------------------

            if self.main_window.mode_manager.get_mode() != "EDIT":

                print("Extrude requires EDIT mode")
                return

            # ---------------------------------
            # Face Mode Check
            # ---------------------------------

            if not self.face_mode:

                print("Extrude requires FACE mode")
                return

            # ---------------------------------
            # Selected Object Check
            # ---------------------------------

            if self.selected_object is None:

                print("No selected object")
                return

            # ---------------------------------
            # Selected Face Check
            # ---------------------------------

            if self.selected_face is None:

                print("No selected face")
                return

            mesh = self.selected_object.mesh

            if mesh is None:

                print("Selected object has no mesh")
                return

            # ---------------------------------
            # Validate Face
            # ---------------------------------

            if self.selected_face < 0:

                print("Invalid selected face")
                return

            if self.selected_face >= len(mesh.faces):

                print("Invalid selected face")
                return

            original_face = list(
                mesh.faces[self.selected_face]
            )

            if len(original_face) < 3:

                print("Invalid face")
                return

            # ---------------------------------
            # Validate Vertices
            # ---------------------------------

            for vertex_index in original_face:

                if vertex_index < 0:

                    print(
                        "Invalid vertex index:",
                        vertex_index
                    )

                    return

                if vertex_index >= len(mesh.vertices):

                    print(
                        "Invalid vertex index:",
                        vertex_index
                    )

                    return

            # ---------------------------------
            # Save State For Undo
            # ---------------------------------

            self.history_manager.save_state(
                self.selected_object
            )

            # ---------------------------------
            # Store Original Vertex Positions
            # ---------------------------------

            self.extrude_original_vertices = []

            for vertex_index in original_face:

                vertex = mesh.vertices[
                    vertex_index
                ]

                self.extrude_original_vertices.append(
                    np.array(
                        vertex,
                        dtype=np.float32
                    )
                )

            # ---------------------------------
            # Calculate Face Normal
            # ---------------------------------

            normal = self.get_face_normal(
                mesh,
                self.selected_face
            )

            print(
                "================================="
            )

            print(
                "Selected Face:",
                self.selected_face
            )

            print(
                "Face Vertices:",
                original_face
            )

            print(
                "Face Normal:",
                normal
            )

            print(
                "================================="
            )

            normal = np.array(
                normal,
                dtype=np.float32
            )

            normal_length = np.linalg.norm(
                normal
            )

            if normal_length < 1e-6:

                print("Invalid face normal")
                return

            normal /= normal_length

            print(
                "Extrude Normal:",
                normal
            )

            # ---------------------------------
            # Start Extrusion
            # ---------------------------------

            self.extrude_mode = True
            self.extrude_dragging = True

            self.extrude_face = (
                self.selected_face
            )

            self.extrude_normal = normal

            # ---------------------------------
            # Initial Distance
            # ---------------------------------

            self.extrude_distance = 0.5

            self.extrude_start_distance = 0.0

            # ---------------------------------
            # Clear Previous Extrusion Data
            # ---------------------------------

            self.extrude_vertex_indices = []

            # ---------------------------------
            # Create Extrusion Geometry
            # ---------------------------------

            old_vertex_count = len(
                mesh.vertices
            )

            self.extrude_selected_faces()

            print(
                "AFTER EXTRUDE | VERTICES:",
                mesh.vertices
            )

            print(
                "AFTER EXRUDE | FACES:",
                mesh.faces
            )

            print(
                "AFTER EXTRUDE | EXTRUDE_VERTICES:",
                self.extrude_vertex_indices
            )

            self.update()

            # ---------------------------------
            # Find New Vertices
            # ---------------------------------

            new_vertex_count = len(
                mesh.vertices
            )

            if new_vertex_count <= old_vertex_count:

                print(
                    "Extrusion failed: no new vertices"
                )

                self.extrude_mode = False
                self.extrude_dragging = False

                return

            self.extrude_vertex_indices = list(
                range(
                    old_vertex_count,
                    new_vertex_count
                )
            )

            print(
                "Extrude Vertices:",
                self.extrude_vertex_indices
            )

            # ---------------------------------
            # Store Mouse Position
            # ---------------------------------

            self.extrude_start_mouse_x = (
                self.mouse_x
            )

            self.extrude_start_mouse_y = (
                self.mouse_y
            )

            self.extrude_axis_origin = None
            self.extrude_start_axis_parameter = 0.0

            print(
                "Extrude Start Mouse:",
                self.extrude_start_mouse_x,
                self.extrude_start_mouse_y
            )

            # ---------------------------------
            # Disable Other Dragging
            # ---------------------------------

            self.face_dragging = False

            self.vertex_dragging = False
            self.edge_dragging = False
            self.dragging_object = False

            self.selected_vertex = None
            self.selected_edge = None

            # ---------------------------------
            # Keep NEW Extruded Face Selected
            # ---------------------------------

            # extrude_selected_face() has already 
            # updated self.selected_face to the 
            # newly-created cap face.

            mesh.selected_face = self.selected_face

            print(
                "Active extruded face:",
                self.selected_face
            )
            # ---------------------------------
            # Initialize Mouse Position
            # ---------------------------------

            self.last_mouse_x = (
                self.mouse_x
            )

            self.last_mouse_y = (
                self.mouse_y
            )

            # ---------------------------------
            # Update Bounding Box
            # ---------------------------------

            if hasattr(
                self.selected_object,
                "bounding_box"
            ):

                self.selected_object.bounding_box.update(
                    self.selected_object.position,
                    self.selected_object.scale
                )

            # ---------------------------------
            # Update Viewport
            # ---------------------------------

            self.update()

            return

        # ---------------------------------
        # F4 OBJECT / EDIT MODE
        # ---------------------------------
        elif event.key() == Qt.Key_F4:

            self.main_window.mode_manager.toggle()

            print(
                self.main_window.mode_manager.get_mode()
            )

            self.update()

            return

        super().keyPressEvent(event)
        
    def pick_object(self):

        if len(self.scene_objects) == 0:
            return None

        ray = RayBuilder.build_ray(
            self.mouse_x,
            self.mouse_y,
            self,
            self.camera
        )

        print("Origin:", ray.origin)
        print("Direction:", ray.direction)

        return self.raycaster.cast(
            ray,
            self.scene_objects
        )

    def event(self, event):

        if event.type() == QEvent.KeyPress:

            if event.key() == Qt.Key_Tab:

                print("TAB DETECTED")

                return True

        return super().event(event)
    
    def pick_vertex(self, obj, ray):

        if obj is None:
            return None

        if obj.mesh is None:
            return None

        nearest = None

        nearest_distance = 0.12

        origin = np.array(ray.origin)

        direction = np.array(ray.direction)

        for index, vertex in enumerate(obj.mesh.vertices):

            world_vertex = np.array(vertex)

            world_vertex *= np.array(obj.scale)

            world_vertex += np.array(obj.position)

            t = np.dot(
                world_vertex - origin,
                direction
            )

            if t < 0:
                continue

            closest = origin + direction * t

            distance = np.linalg.norm(
                world_vertex - closest
            )

            if distance < nearest_distance:

                nearest_distance = distance

                nearest = index

        return nearest

    def pick_edge(
        self,
        obj,
        ray
    ):

        if obj is None:
            return None

        if obj.mesh is None:
            return None

        if not hasattr(obj.mesh, "edges"):
            return None

        threshold = 0.10

        closest_edge = None
        closest_distance = 999999.0

        for i, edge in enumerate(obj.mesh.edges):

            a = np.array(
                obj.mesh.vertices[edge[0]],
                dtype=np.float32
            )

            b = np.array(
                obj.mesh.vertices[edge[1]],
                dtype=np.float32
            )

            # -------------------------
            # Local → World
            # -------------------------

            a *= np.array(obj.scale)

            b *= np.array(obj.scale)

            a += np.array(obj.position)

            b += np.array(obj.position)

            print("Edge", i)
            print("A:", a)
            print("B:", b)
            print("Ray Origin:", ray.origin)
            print("Ray Dir:", ray.direction)

            distance = GeometryUtils.distance_ray_to_segment(
                ray,
                a,
                b
            )

            if distance < threshold:

                if distance < closest_distance:

                    closest_distance = distance
                    closest_edge = i

        return closest_edge

    def ray_triangle_intersect(
        self,
        ray,
        v0,
        v1,
        v2
    ):

        epsilon = 1e-6

        edge1 = v1 - v0
        edge2 = v2 - v0

        h = np.cross(ray.direction, edge2)
        a = np.dot(edge1, h)

        if -epsilon < a < epsilon:
            return None

        f = 1.0 / a

        s = ray.origin - v0

        u = f * np.dot(s, h)

        if u < 0.0 or u > 1.0:
            return None

        q = np.cross(s, edge1)

        v = f * np.dot(ray.direction, q)

        if v < 0.0 or (u + v) > 1.0:
            return None

        t = f * np.dot(edge2, q)

        if t > epsilon:
            return t

        return None

    def pick_face(
        self,
        obj,
        ray
    ):

        if obj is None:
            return None

        if obj.mesh is None:
            return None

        closest_distance = float("inf")
        closest_face = None

        for face_index, face in enumerate(obj.mesh.faces):

            # -------------------------
            # Triangle
            # -------------------------

            if len(face) == 3:

                v0 = np.array(obj.mesh.vertices[face[0]], dtype=np.float32)
                v1 = np.array(obj.mesh.vertices[face[1]], dtype=np.float32)
                v2 = np.array(obj.mesh.vertices[face[2]], dtype=np.float32)

                v0 += obj.position
                v1 += obj.position
                v2 += obj.position

                distance = self.ray_triangle_intersect(
                    ray,
                    v0,
                    v1,
                    v2
                )

                if distance is not None:

                    if distance < closest_distance:

                        closest_distance = distance
                        closest_face = face_index

            # -------------------------
            # Quad
            # -------------------------

            elif len(face) == 4:

                v0 = np.array(obj.mesh.vertices[face[0]], dtype=np.float32)
                v1 = np.array(obj.mesh.vertices[face[1]], dtype=np.float32)
                v2 = np.array(obj.mesh.vertices[face[2]], dtype=np.float32)
                v3 = np.array(obj.mesh.vertices[face[3]], dtype=np.float32)

                v0 += obj.position
                v1 += obj.position
                v2 += obj.position
                v3 += obj.position

                d1 = self.ray_triangle_intersect(
                    ray,
                    v0,
                    v1,
                    v2
                )

                d2 = self.ray_triangle_intersect(
                    ray,
                    v0,
                    v2,
                    v3
                )

                if d1 is not None:

                    if d1 < closest_distance:

                        closest_distance = d1
                        closest_face = face_index

                if d2 is not None:

                    if d2 < closest_distance:

                        closest_distance = d2
                        closest_face = face_index

        return closest_face

    def set_vertex_mode(self):

        self.vertex_mode = True
        self.edge_mode = False
        self.face_mode = False

        self.selected_edge = None
        self.selected_edges.clear()
        self.selected_face = None
        self.selected_faces.clear()

        self.update()

    def set_edge_mode(self):

        self.vertex_mode = False
        self.edge_mode = True
        self.face_mode = False

        self.selected_vertex = None
        self.selected_vertices.clear()
        self.selected_face = None
        self.selected_faces.clear()

        self.update()

    def set_face_mode(self):

        self.vertex_mode = False
        self.edge_mode = False
        self.face_mode = True

        self.selected_vertex = None
        self.selected_vertices.clear()
        self.selected_edge = None
        self.selected_edges.clear()

        self.update()

