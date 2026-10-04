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

        self.hand_cursor_x = None
        self.hand_cursor_y = None
        self.hand_cursor_visible = False
        self.hand_hovered_object = None

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
        # Loop Cut Sliding
        # ---------------------------------

        # Maps each newly-created loop-cut vertex to the original edge
        # it was created on. This allows the loop to slide along the
        # original topology instead of translating the loop off the mesh.
        self.loop_cut_vertex_sources = {}

        self.loop_cut_dragging = False
        self.loop_cut_original_positions = {}
        self.loop_cut_start_parameters = {}
        self.loop_cut_start_mouse_x = 0
        self.loop_cut_start_mouse_y = 0

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

    def inset_selected_face(self, inset_ratio=0.20):
        """
        Inset the active face by scaling its vertices toward the face
        centroid and creating a new inner face surrounded by side faces.

        This first implementation intentionally operates on one selected
        face. The resulting inner face becomes the active selection so it
        can immediately be extruded.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("INSET: Requires EDIT mode")
                return False

        if not self.face_mode:
            print("INSET: Requires FACE mode")
            return False

        if self.selected_object is None:
            print("INSET: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("INSET: Selected object has no mesh")
            return False

        face_index = self.selected_face

        if face_index is None:
            print("INSET: No selected face")
            return False

        if face_index < 0 or face_index >= len(mesh.faces):
            print("INSET: Invalid selected face")
            return False

        original_face = list(mesh.faces[face_index])

        if len(original_face) < 3:
            print("INSET: Face has fewer than 3 vertices")
            return False

        try:
            inset_ratio = float(inset_ratio)
        except (TypeError, ValueError):
            print("INSET: Invalid inset amount")
            return False

        if inset_ratio <= 0.0 or inset_ratio >= 1.0:
            print("INSET: Amount must be between 0 and 1")
            return False

        # Validate all original vertex indices before changing the mesh.
        for vertex_index in original_face:
            if vertex_index < 0 or vertex_index >= len(mesh.vertices):
                print("INSET: Invalid vertex index:", vertex_index)
                return False

        # Save one undo state for the complete inset operation.
        if self.history_manager is not None:
            self.history_manager.save_state(
                self.selected_object
            )

        # ---------------------------------
        # Face centroid
        # ---------------------------------

        positions = np.array(
            [mesh.vertices[index] for index in original_face],
            dtype=np.float32
        )

        center = np.mean(
            positions,
            axis=0
        )

        # inset_ratio is the amount removed from the outside.
        # Example: 0.20 keeps 80% of the distance to the centroid.
        scale = 1.0 - inset_ratio

        new_vertices = []

        for vertex in positions:
            new_vertex = center + (vertex - center) * scale

            mesh.vertices.append([
                float(new_vertex[0]),
                float(new_vertex[1]),
                float(new_vertex[2])
            ])

            new_vertices.append(
                len(mesh.vertices) - 1
            )

        # ---------------------------------
        # Build the inset ring
        # ---------------------------------

        ring_faces = []
        count = len(original_face)

        for i in range(count):
            outer_a = original_face[i]
            outer_b = original_face[(i + 1) % count]
            inner_b = new_vertices[(i + 1) % count]
            inner_a = new_vertices[i]

            ring_faces.append(
                (outer_a, outer_b, inner_b, inner_a)
            )

        # The inner face keeps the original winding order.
        inner_face = tuple(new_vertices)

        # Replace the original face with the ring and append the inner face.
        mesh.faces[face_index:face_index + 1] = ring_faces

        inner_face_index = len(mesh.faces)
        mesh.faces.append(inner_face)

        # ---------------------------------
        # Rebuild topology
        # ---------------------------------

        mesh.build_edges()

        # ---------------------------------
        # Keep the new inner face selected
        # ---------------------------------

        self.selected_face = inner_face_index
        self.selected_faces = {
            inner_face_index
        }

        mesh.selected_face = inner_face_index

        self.selected_vertex = None
        self.selected_vertices.clear()
        self.selected_edge = None
        self.selected_edges.clear()

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False
        self.dragging_object = False

        self.update()

        print(
            "INSET COMPLETE | Face:",
            face_index,
            "-> Inner Face:",
            inner_face_index
        )
        print(
            "Vertices :",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True

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


    def paintEvent(self, event):

        super().paintEvent(event)

        self.draw_hand_cursor_overlay()

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

    def update_hand_cursor_screen(self, x, y):

        smooth = 0.25

        if self.hand_cursor_x is None:
            self.hand_cursor_x = x
            self.hand_cursor_y = y
        else:
            self.hand_cursor_x += (
                x - self.hand_cursor_x
            ) * smooth

            self.hand_cursor_y += (
                y - self.hand_cursor_y
            ) * smooth

        self.hand_cursor_visible = True

        self.mouse_x = self.hand_cursor_x
        self.mouse_y = self.hand_cursor_y

        self.update()

    def pick_object_at_hand_cursor(self):

        if not self.hand_cursor_visible:
            return None

        if self.hand_cursor_x is None:
            return None

        if self.hand_cursor_y is None:
            return None

        if not self.scene_objects:
            return None

        if self.main_window is not None:

            interaction = getattr(
                self.main_window,
                "interaction",
                None
            )

            if interaction is not None and getattr(
                interaction,
                "is_holding",
                False
            ):
                return self.selected_object

        ray = RayBuilder.build_ray(
            self.hand_cursor_x,
            self.hand_cursor_y,
            self,
            self.camera
        )

        picked = self.raycaster.cast(
            ray,
            self.scene_objects
        )

        if picked is not self.hand_hovered_object:

            self.hand_hovered_object = picked

            if picked is not None:
                self.set_selected_object(picked)
                print(
                    "HAND PICKED OBJECT:",
                    picked.name
                )
            else:
                self.selection_manager.deselect()
                print("HAND PICKED OBJECT: None")

        return picked

    def draw_hand_cursor_overlay(self):

        if not self.hand_cursor_visible:
            return

        if self.hand_cursor_x is None:
            return

        if self.hand_cursor_y is None:
            return

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.setPen(
            Qt.cyan
        )

        painter.setBrush(
            Qt.NoBrush
        )

        painter.drawEllipse(
            int(self.hand_cursor_x) - 9,
            int(self.hand_cursor_y) - 9,
            18,
            18
        )

        painter.end()

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

                                # If the selected edge belongs to the loop
                                # created by Loop Cut, drag the entire loop
                                # using constrained edge sliding.
                                selected_loop_vertices = set()

                                for selected_edge_index in (
                                    self.selected_edges
                                ):

                                    if (
                                        selected_edge_index < 0
                                        or selected_edge_index >= len(
                                            obj.mesh.edges
                                        )
                                    ):
                                        continue

                                    selected_mesh_edge = (
                                        obj.mesh.edges[
                                            selected_edge_index
                                        ]
                                    )

                                    if len(selected_mesh_edge) != 2:
                                        continue

                                    selected_loop_vertices.add(
                                        int(selected_mesh_edge[0])
                                    )
                                    selected_loop_vertices.add(
                                        int(selected_mesh_edge[1])
                                    )

                                loop_vertices = {
                                    vertex_index
                                    for vertex_index in selected_loop_vertices
                                    if vertex_index in
                                    self.loop_cut_vertex_sources
                                }

                                if (
                                    loop_vertices
                                    and loop_vertices == selected_loop_vertices
                                ):

                                    self.loop_cut_dragging = True

                                    self.loop_cut_original_positions = {}
                                    self.loop_cut_start_parameters = {}

                                    for vertex_index in loop_vertices:

                                        original_position = np.array(
                                            obj.mesh.vertices[
                                                vertex_index
                                            ],
                                            dtype=np.float64
                                        )

                                        self.loop_cut_original_positions[
                                            vertex_index
                                        ] = original_position.copy()

                                        a, b = (
                                            self.loop_cut_vertex_sources[
                                                vertex_index
                                            ]
                                        )

                                        if (
                                            a >= 0
                                            and b >= 0
                                            and a < len(obj.mesh.vertices)
                                            and b < len(obj.mesh.vertices)
                                        ):

                                            va = np.array(
                                                obj.mesh.vertices[a],
                                                dtype=np.float64
                                            )

                                            vb = np.array(
                                                obj.mesh.vertices[b],
                                                dtype=np.float64
                                            )

                                            edge_vector = vb - va
                                            length_squared = float(
                                                np.dot(
                                                    edge_vector,
                                                    edge_vector
                                                )
                                            )

                                            if length_squared > 1e-12:

                                                parameter = float(
                                                    np.dot(
                                                        original_position - va,
                                                        edge_vector
                                                    )
                                                    / length_squared
                                                )

                                                self.loop_cut_start_parameters[
                                                    vertex_index
                                                ] = parameter

                                    self.loop_cut_start_mouse_x = event.x()
                                    self.loop_cut_start_mouse_y = event.y()

                                else:

                                    self.loop_cut_dragging = False
                                    self.loop_cut_original_positions = {}
                                    self.loop_cut_start_parameters = {}

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

            self.loop_cut_dragging = False
            self.loop_cut_original_positions = {}
            self.loop_cut_start_parameters = {}

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
        # LOOP CUT SLIDE
        # ---------------------------------

        if (
            self.loop_cut_dragging
            and self.selected_object is not None
            and self.main_window.mode_manager.get_mode() == "EDIT"
        ):

            mesh = self.selected_object.mesh

            if mesh is None:
                return

            # -------------------------------------------------------------
            # LOOP SLIDE
            # -------------------------------------------------------------
            # The old implementation used only screen X movement. That
            # makes the loop appear to rotate when the supporting edges are
            # vertical or diagonal on screen.
            #
            # Instead, project each original supporting edge into screen
            # space and measure the mouse movement along that projected
            # edge. The resulting value changes only the vertex parameter
            # on that edge.
            # -------------------------------------------------------------

            mouse_delta = np.array(
                [
                    float(event.x() - self.loop_cut_start_mouse_x),
                    float(event.y() - self.loop_cut_start_mouse_y)
                ],
                dtype=np.float64
            )

            obj = self.selected_object

            try:
                self.makeCurrent()

                glMatrixMode(GL_PROJECTION)
                glPushMatrix()
                glLoadIdentity()

                width = max(1, self.width())
                height = max(1, self.height())

                gluPerspective(
                    45.0,
                    width / height,
                    0.1,
                    100.0
                )

                glMatrixMode(GL_MODELVIEW)
                glPushMatrix()
                glLoadIdentity()

                self.camera.apply()

                # Apply exactly the same object transform used by
                # draw_scene_object(). This makes the projected supporting
                # edge direction match what the user sees on screen.
                glTranslatef(
                    float(obj.position[0]),
                    float(obj.position[1]),
                    float(obj.position[2])
                )

                glRotatef(
                    float(obj.rotation[0]),
                    1.0,
                    0.0,
                    0.0
                )

                glRotatef(
                    float(obj.rotation[1]),
                    0.0,
                    1.0,
                    0.0
                )

                glRotatef(
                    float(obj.rotation[2]),
                    0.0,
                    0.0,
                    1.0
                )

                glScalef(
                    float(obj.scale[0]),
                    float(obj.scale[1]),
                    float(obj.scale[2])
                )

                model_matrix = glGetDoublev(
                    GL_MODELVIEW_MATRIX
                )

                projection_matrix = glGetDoublev(
                    GL_PROJECTION_MATRIX
                )

                viewport = glGetIntegerv(
                    GL_VIEWPORT
                )

                projected_edges = {}

                for vertex_index, source_edge in (
                    self.loop_cut_vertex_sources.items()
                ):

                    if vertex_index not in self.loop_cut_original_positions:
                        continue

                    a, b = source_edge

                    if (
                        a < 0
                        or b < 0
                        or a >= len(mesh.vertices)
                        or b >= len(mesh.vertices)
                    ):
                        continue

                    va = np.array(
                        mesh.vertices[a],
                        dtype=np.float64
                    )

                    vb = np.array(
                        mesh.vertices[b],
                        dtype=np.float64
                    )

                    try:
                        screen_a = np.array(
                            gluProject(
                                float(va[0]),
                                float(va[1]),
                                float(va[2]),
                                model_matrix,
                                projection_matrix,
                                viewport
                            ),
                            dtype=np.float64
                        )

                        screen_b = np.array(
                            gluProject(
                                float(vb[0]),
                                float(vb[1]),
                                float(vb[2]),
                                model_matrix,
                                projection_matrix,
                                viewport
                            ),
                            dtype=np.float64
                        )

                    except Exception:
                        continue

                    screen_vector = screen_b[:2] - screen_a[:2]

                    # OpenGL uses bottom-up screen Y; Qt mouse coordinates
                    # use top-down screen Y.
                    screen_vector[1] = -screen_vector[1]

                    screen_length = float(
                        np.linalg.norm(screen_vector)
                    )

                    if screen_length < 1e-6:
                        continue

                    screen_direction = (
                        screen_vector / screen_length
                    )

                    projected_edges[vertex_index] = (
                        screen_direction,
                        screen_length
                    )

                # Restore OpenGL state before modifying the mesh.
                glMatrixMode(GL_MODELVIEW)
                glPopMatrix()

                glMatrixMode(GL_PROJECTION)
                glPopMatrix()

                glMatrixMode(GL_MODELVIEW)

                self.doneCurrent()

            except Exception as error:
                print(
                    "LOOP CUT SLIDE PROJECTION ERROR:",
                    error
                )

                try:
                    self.doneCurrent()
                except Exception:
                    pass

            for vertex_index, source_edge in (
                self.loop_cut_vertex_sources.items()
            ):

                if vertex_index not in self.loop_cut_original_positions:
                    continue

                a, b = source_edge

                if (
                    a < 0
                    or b < 0
                    or a >= len(mesh.vertices)
                    or b >= len(mesh.vertices)
                ):
                    continue

                original_position = np.array(
                    self.loop_cut_original_positions[
                        vertex_index
                    ],
                    dtype=np.float64
                )

                edge_start = np.array(
                    mesh.vertices[a],
                    dtype=np.float64
                )

                edge_end = np.array(
                    mesh.vertices[b],
                    dtype=np.float64
                )

                edge_vector = edge_end - edge_start

                edge_length_squared = float(
                    np.dot(
                        edge_vector,
                        edge_vector
                    )
                )

                if edge_length_squared < 1e-12:
                    continue

                start_parameter = self.loop_cut_start_parameters.get(
                    vertex_index,
                    0.5
                )

                projection_data = projected_edges.get(
                    vertex_index
                )

                if projection_data is None:
                    continue

                screen_direction, screen_length = projection_data

                # Mouse movement is converted into the fraction of the
                # supporting edge travelled on screen. The 0.85 factor
                # keeps the motion controlled on small edges.
                mouse_along_edge = float(
                    np.dot(
                        mouse_delta,
                        screen_direction
                    )
                )

                parameter_delta = (
                    mouse_along_edge
                    / max(screen_length, 1.0)
                    * 0.85
                )

                parameter = max(
                    0.02,
                    min(
                        0.98,
                        start_parameter + parameter_delta
                    )
                )

                new_position = (
                    edge_start
                    + edge_vector * parameter
                )

                mesh.vertices[vertex_index] = [
                    float(new_position[0]),
                    float(new_position[1]),
                    float(new_position[2])
                ]

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

                if edge_index >= len(mesh.edges):
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

    def dissolve_selected_edge(self):
        """
        Dissolve the active selected manifold edge by removing the edge and
        joining its two incident faces into one polygon.

        The edge must belong to exactly two faces. The two faces are replaced
        by the boundary that remains after their shared edge is removed.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("DISSOLVE EDGE: Requires EDIT mode")
                return False

        if not self.edge_mode:
            print("DISSOLVE EDGE: Requires EDGE mode")
            return False

        if self.selected_object is None:
            print("DISSOLVE EDGE: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("DISSOLVE EDGE: Selected object has no mesh")
            return False

        edge_index = self.selected_edge

        if edge_index is None and self.selected_edges:
            edge_index = next(iter(self.selected_edges))

        if edge_index is None:
            print("DISSOLVE EDGE: No selected edge")
            return False

        if edge_index < 0 or edge_index >= len(mesh.edges):
            print("DISSOLVE EDGE: Invalid selected edge")
            return False

        edge = tuple(int(v) for v in mesh.edges[edge_index])
        if len(edge) != 2 or edge[0] == edge[1]:
            print("DISSOLVE EDGE: Invalid edge data")
            return False

        a, b = edge
        target = {a, b}

        incident = []
        for face_index, face in enumerate(mesh.faces):
            if face is None or len(face) < 3:
                continue
            found = False
            for i in range(len(face)):
                u = int(face[i])
                v = int(face[(i + 1) % len(face)])
                if {u, v} == target:
                    found = True
                    break
            if found:
                incident.append(face_index)

        if len(incident) != 2:
            print("DISSOLVE EDGE: Edge must have exactly two incident faces")
            return False

        face_a = [int(v) for v in mesh.faces[incident[0]]]
        face_b = [int(v) for v in mesh.faces[incident[1]]]

        def boundary_path(face, start, end):
            """Return the path start -> end around face excluding start/end edge."""
            n = len(face)
            try:
                si = face.index(start)
                ei = face.index(end)
            except ValueError:
                return None

            # Walk forward around the face. The direct start->end edge must
            # not be used, so reject the path when they are adjacent forward.
            path = [start]
            i = si
            while True:
                i = (i + 1) % n
                path.append(face[i])
                if face[i] == end:
                    break
                if len(path) > n + 1:
                    return None

            if len(path) == 2:
                # Direct shared edge; use the other direction instead.
                path = [start]
                i = si
                while True:
                    i = (i - 1) % n
                    path.append(face[i])
                    if face[i] == end:
                        break
                    if len(path) > n + 1:
                        return None

            return path

        # Choose the non-shared boundary path on each face. One face runs
        # from a to b; the other runs from b to a.
        path_a = boundary_path(face_a, a, b)
        path_b = boundary_path(face_b, b, a)

        if path_a is None or path_b is None:
            print("DISSOLVE EDGE: Could not construct merged boundary")
            return False

        merged_face = path_a[:-1] + path_b[:-1]

        # Remove accidental repeated vertices while preserving boundary order.
        cleaned = []
        for vertex in merged_face:
            if not cleaned or cleaned[-1] != vertex:
                cleaned.append(vertex)

        if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
            cleaned.pop()

        if len(cleaned) < 3 or len(set(cleaned)) < 3:
            print("DISSOLVE EDGE: Resulting face would be degenerate")
            return False

        if self.history_manager is not None:
            self.history_manager.save_state(self.selected_object)

        new_faces = []
        for face_index, face in enumerate(mesh.faces):
            if face_index in incident:
                continue
            new_faces.append(tuple(int(v) for v in face))

        new_faces.append(tuple(cleaned))
        mesh.faces = new_faces
        mesh.build_edges()

        # The dissolved edge no longer exists. Keep the resulting face active.
        self.selected_edge = None
        self.selected_edges.clear()
        self.selected_face = len(mesh.faces) - 1
        self.selected_faces = {self.selected_face}

        self.selected_vertex = None
        self.selected_vertices.clear()

        mesh.selected_edge = None
        mesh.selected_face = self.selected_face
        mesh.selected_vertex = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.update()

        print(
            "DISSOLVE EDGE COMPLETE | Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True

    def dissolve_selected_face(self):
        """
        Dissolve the currently selected face or selected face group.

        The selected face records are removed while vertices that are still
        referenced by surrounding faces are preserved. The derived edge list
        is rebuilt from the remaining faces, leaving an open boundary where
        the dissolved face was.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("DISSOLVE FACE: Requires EDIT mode")
                return False

        if not self.face_mode:
            print("DISSOLVE FACE: Requires FACE mode")
            return False

        if self.selected_object is None:
            print("DISSOLVE FACE: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("DISSOLVE FACE: Selected object has no mesh")
            return False

        selected = set(
            int(index)
            for index in self.selected_faces
            if index is not None
        )

        if self.selected_face is not None:
            selected.add(int(self.selected_face))

        selected = {
            index
            for index in selected
            if 0 <= index < len(mesh.faces)
        }

        if not selected:
            print("DISSOLVE FACE: No selected face")
            return False

        if self.history_manager is not None:
            self.history_manager.save_state(
                self.selected_object
            )

        print(
            "DISSOLVE FACE:",
            sorted(selected)
        )

        # Remove only the selected faces. Vertices are not deleted here;
        # surrounding faces may still reference them and therefore preserve
        # the boundary of the opened surface.
        mesh.faces = [
            tuple(int(vertex) for vertex in face)
            for index, face in enumerate(mesh.faces)
            if index not in selected
        ]

        # Repair invalid/unused topology and rebuild derived edges.
        self._cleanup_mesh_after_deletion(mesh)

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.edge_vertex_a = None
        self.edge_vertex_b = None

        self.vertex_original = None
        self.face_original_vertices = None

        self.update()

        print(
            "DISSOLVE FACE COMPLETE | Faces:",
            len(mesh.faces),
            "| Vertices:",
            len(mesh.vertices),
            "| Edges:",
            len(mesh.edges)
        )

        return True

    def dissolve_selected_vertex(self):
        """
        Dissolve the currently selected vertex without deleting the surface
        around it when the surrounding topology forms a valid manifold link.

        The faces incident to the vertex are removed and replaced by one
        polygon made from the surrounding neighboring vertices. This keeps
        the surface filled instead of creating the open hole produced by a
        normal vertex deletion.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("DISSOLVE VERTEX: Requires EDIT mode")
                return False

        if not self.vertex_mode:
            print("DISSOLVE VERTEX: Requires VERTEX mode")
            return False

        if self.selected_object is None:
            print("DISSOLVE VERTEX: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("DISSOLVE VERTEX: Selected object has no mesh")
            return False

        vertex_index = self.selected_vertex

        if vertex_index is None and self.selected_vertices:
            vertex_index = sorted(self.selected_vertices)[0]

        if vertex_index is None:
            print("DISSOLVE VERTEX: No selected vertex")
            return False

        if (
            vertex_index < 0
            or vertex_index >= len(mesh.vertices)
        ):
            print("DISSOLVE VERTEX: Invalid vertex")
            return False

        # ---------------------------------
        # Find all faces connected to the vertex
        # ---------------------------------

        incident_faces = []

        for face_index, face in enumerate(mesh.faces):
            if vertex_index in face:
                incident_faces.append(face_index)

        if len(incident_faces) < 3:
            print(
                "DISSOLVE VERTEX: Vertex needs at least 3 incident faces"
            )
            return False

        # ---------------------------------
        # Build the vertex-link graph.
        # Each incident face contributes an edge between the two vertices
        # directly adjacent to the selected vertex.
        # ---------------------------------

        link_edges = set()
        neighbors = set()

        for face_index in incident_faces:

            face = list(mesh.faces[face_index])
            local_index = face.index(vertex_index)
            face_length = len(face)

            previous_vertex = int(
                face[(local_index - 1) % face_length]
            )
            next_vertex = int(
                face[(local_index + 1) % face_length]
            )

            if previous_vertex == vertex_index or next_vertex == vertex_index:
                print(
                    "DISSOLVE VERTEX: Invalid face topology"
                )
                return False

            neighbors.add(previous_vertex)
            neighbors.add(next_vertex)

            if previous_vertex != next_vertex:
                link_edges.add(
                    tuple(sorted((previous_vertex, next_vertex)))
                )

        if len(neighbors) < 3:
            print(
                "DISSOLVE VERTEX: Surrounding topology is degenerate"
            )
            return False

        # A manifold interior vertex has a closed link where every neighbor
        # has exactly two link connections.
        adjacency = {
            vertex: set()
            for vertex in neighbors
        }

        for a, b in link_edges:
            adjacency[a].add(b)
            adjacency[b].add(a)

        if any(
            len(adjacency[vertex]) != 2
            for vertex in neighbors
        ):
            print(
                "DISSOLVE VERTEX: Requires a closed manifold vertex"
            )
            return False

        # ---------------------------------
        # Walk the closed vertex link into polygon order
        # ---------------------------------

        start = min(neighbors)
        polygon_vertices = [start]
        previous = None
        current = start

        while True:

            candidates = [
                neighbor
                for neighbor in adjacency[current]
                if neighbor != previous
            ]

            if not candidates:
                print(
                    "DISSOLVE VERTEX: Could not build surrounding polygon"
                )
                return False

            next_vertex = min(candidates)

            if next_vertex == start:
                break

            if next_vertex in polygon_vertices:
                print(
                    "DISSOLVE VERTEX: Invalid surrounding topology"
                )
                return False

            polygon_vertices.append(next_vertex)
            previous = current
            current = next_vertex

            if len(polygon_vertices) > len(neighbors):
                print(
                    "DISSOLVE VERTEX: Could not close surrounding polygon"
                )
                return False

        if len(polygon_vertices) != len(neighbors):
            print(
                "DISSOLVE VERTEX: Incomplete surrounding polygon"
            )
            return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:
            self.history_manager.save_state(
                self.selected_object
            )

        # ---------------------------------
        # Preserve the approximate original surface orientation.
        # ---------------------------------

        average_normal = np.zeros(3, dtype=np.float32)

        for face_index in incident_faces:

            face = mesh.faces[face_index]

            if len(face) < 3:
                continue

            a = np.array(
                mesh.vertices[face[0]],
                dtype=np.float32
            )
            b = np.array(
                mesh.vertices[face[1]],
                dtype=np.float32
            )
            c = np.array(
                mesh.vertices[face[2]],
                dtype=np.float32
            )

            average_normal += np.cross(
                b - a,
                c - a
            )

        if np.linalg.norm(average_normal) > 1e-8:
            average_normal = (
                average_normal
                / np.linalg.norm(average_normal)
            )

            p0 = np.array(
                mesh.vertices[polygon_vertices[0]],
                dtype=np.float32
            )
            p1 = np.array(
                mesh.vertices[polygon_vertices[1]],
                dtype=np.float32
            )
            p2 = np.array(
                mesh.vertices[polygon_vertices[2]],
                dtype=np.float32
            )

            polygon_normal = np.cross(
                p1 - p0,
                p2 - p0
            )

            if (
                np.linalg.norm(polygon_normal) > 1e-8
                and np.dot(polygon_normal, average_normal) < 0.0
            ):
                polygon_vertices.reverse()

        # ---------------------------------
        # Replace the incident faces with the dissolved polygon
        # ---------------------------------

        incident_set = set(incident_faces)

        new_faces = [
            tuple(face)
            for face_index, face in enumerate(mesh.faces)
            if face_index not in incident_set
        ]

        new_faces.append(
            tuple(polygon_vertices)
        )

        mesh.faces = new_faces

        # ---------------------------------
        # Remove the dissolved vertex and remap indices
        # ---------------------------------

        mesh.vertices.pop(vertex_index)

        remapped_faces = []

        for face in mesh.faces:

            remapped = []

            for index in face:
                if index > vertex_index:
                    index -= 1
                remapped.append(index)

            if len(remapped) >= 3 and len(set(remapped)) >= 3:
                remapped_faces.append(tuple(remapped))

        mesh.faces = remapped_faces
        mesh.build_edges()

        # ---------------------------------
        # Clear edit selections
        # ---------------------------------

        self.selected_vertices.clear()
        self.selected_vertex = None

        self.selected_edge = None
        self.selected_edges.clear()

        self.selected_face = None
        self.selected_faces.clear()

        mesh.selected_vertex = None
        mesh.selected_edge = None
        mesh.selected_face = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.update()

        print(
            "DISSOLVE VERTEX COMPLETE | Removed Vertex:",
            vertex_index,
            "| Remaining Vertices:",
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

    def loop_cut_selected_edge(self):

        """
        Insert one centered loop cut through the selected edge loop.

        The current mesh topology is face-authoritative, so the loop is
        discovered from quad faces and the derived edge list is rebuilt
        after the operation. Non-quad faces are left untouched.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("LOOP CUT: Requires EDIT mode")
                return False

        if not self.edge_mode:
            print("LOOP CUT: Requires EDGE mode")
            return False

        if self.selected_object is None:
            print("LOOP CUT: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("LOOP CUT: Selected object has no mesh")
            return False

        edge_index = self.selected_edge

        if edge_index is None:
            print("LOOP CUT: No selected edge")
            return False

        if edge_index < 0 or edge_index >= len(mesh.edges):
            print("LOOP CUT: Invalid selected edge")
            return False

        selected_edge = tuple(mesh.edges[edge_index])

        if len(selected_edge) != 2:
            print("LOOP CUT: Invalid edge")
            return False

        start_edge = (
            int(selected_edge[0]),
            int(selected_edge[1])
        )

        # Work from a stable copy of the original topology.
        original_faces = [
            tuple(int(index) for index in face)
            for face in mesh.faces
            if face is not None
        ]

        # A loop cut is currently defined for quad topology.
        if not any(
            len(face) == 4 and
            start_edge[0] in face and
            start_edge[1] in face
            for face in original_faces
        ):
            print("LOOP CUT: Selected edge is not part of a quad face")
            return False

        # ---------------------------------
        # Find the complete edge loop
        # ---------------------------------

        def canonical(edge):
            a, b = int(edge[0]), int(edge[1])
            return (a, b) if a < b else (b, a)

        def edge_in_face(face, edge):
            a, b = edge
            count = len(face)
            for i in range(count):
                x = face[i]
                y = face[(i + 1) % count]
                if (x == a and y == b) or (x == b and y == a):
                    return True
            return False

        def opposite_edge(face, edge):
            if len(face) != 4:
                return None

            a, b = edge

            for i in range(4):
                x = face[i]
                y = face[(i + 1) % 4]

                if (x == a and y == b) or (x == b and y == a):
                    return (
                        face[(i + 2) % 4],
                        face[(i + 3) % 4]
                    )

            return None

        loop_edges = set()
        queue = [canonical(start_edge)]

        while queue:
            current = queue.pop(0)

            if current in loop_edges:
                continue

            loop_edges.add(current)

            for face in original_faces:
                if len(face) != 4:
                    continue

                if not edge_in_face(face, current):
                    continue

                opposite = opposite_edge(face, current)

                if opposite is None:
                    continue

                opposite = canonical(opposite)

                if opposite not in loop_edges:
                    queue.append(opposite)

        if not loop_edges:
            print("LOOP CUT: Could not build loop")
            return False

        # Every loop edge must belong to at least one quad. This prevents
        # modifying a partial/non-manifold topology accidentally.
        for edge in loop_edges:
            if not any(
                len(face) == 4 and edge_in_face(face, edge)
                for face in original_faces
            ):
                print("LOOP CUT: Incomplete quad loop")
                return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:
            self.history_manager.save_state(
                self.selected_object
            )

        # ---------------------------------
        # Create one midpoint vertex per loop edge
        # ---------------------------------

        # Replace metadata from any previous loop cut.
        self.loop_cut_vertex_sources = {}

        midpoint_indices = {}

        for edge in loop_edges:
            a, b = edge

            if (
                a < 0 or
                b < 0 or
                a >= len(mesh.vertices) or
                b >= len(mesh.vertices)
            ):
                print("LOOP CUT: Invalid loop vertex")
                return False

            va = np.array(
                mesh.vertices[a],
                dtype=np.float32
            )

            vb = np.array(
                mesh.vertices[b],
                dtype=np.float32
            )

            midpoint = (va + vb) * 0.5

            mesh.vertices.append([
                float(midpoint[0]),
                float(midpoint[1]),
                float(midpoint[2])
            ])

            midpoint_index = len(mesh.vertices) - 1

            midpoint_indices[edge] = midpoint_index

            # Remember the original edge so the new loop can later be
            # slid along the existing surface instead of simply translating
            # its vertices in world space.
            self.loop_cut_vertex_sources[midpoint_index] = (
                int(a),
                int(b)
            )

        # ---------------------------------
        # Split every crossed quad
        # ---------------------------------

        new_faces = []
        new_loop_edge_pairs = set()
        cut_faces = 0

        for face in original_faces:

            if len(face) != 4:
                new_faces.append(face)
                continue

            crossed_edges = []

            for i in range(4):
                edge = canonical((
                    face[i],
                    face[(i + 1) % 4]
                ))

                if edge in midpoint_indices:
                    crossed_edges.append(edge)

            # A valid loop-cut face has exactly two opposite cut edges.
            if len(crossed_edges) != 2:
                new_faces.append(face)
                continue

            edge_a, edge_b = crossed_edges

            # Find the positions of the two cut edges in the quad.
            cut_positions = []

            for i in range(4):
                edge = canonical((
                    face[i],
                    face[(i + 1) % 4]
                ))

                if edge == edge_a or edge == edge_b:
                    cut_positions.append(i)

            if len(cut_positions) != 2:
                new_faces.append(face)
                continue

            i0, i1 = sorted(cut_positions)

            # Opposite edges in a quad are separated by two positions.
            if (i1 - i0) not in (2,):
                new_faces.append(face)
                continue

            m0 = midpoint_indices[
                canonical((
                    face[i0],
                    face[(i0 + 1) % 4]
                ))
            ]

            m1 = midpoint_indices[
                canonical((
                    face[i1],
                    face[(i1 + 1) % 4]
                ))
            ]

            # Rotate the face so the first cut edge is (v0,v1).
            rotated = [
                face[(i0 + offset) % 4]
                for offset in range(4)
            ]

            v0, v1, v2, v3 = rotated

            # m0 lies between v0-v1 and m1 between v2-v3.
            new_loop_edge_pairs.add(
                canonical((m0, m1))
            )

            new_faces.append((
                v0,
                m0,
                m1,
                v3
            ))

            new_faces.append((
                m0,
                v1,
                v2,
                m1
            ))

            cut_faces += 1

        if cut_faces == 0:
            print("LOOP CUT: No quad faces were split")
            return False

        mesh.faces = new_faces
        mesh.build_edges()

        # Select the newly created loop edges.
        new_selected_edges = set()

        for i, edge in enumerate(mesh.edges):
            if canonical(edge) in new_loop_edge_pairs:
                new_selected_edges.add(i)

        self.selected_edges = new_selected_edges

        if self.selected_edges:
            self.selected_edge = next(
                iter(self.selected_edges)
            )
        else:
            self.selected_edge = None

        self.selected_vertex = None
        self.selected_vertices.clear()
        self.selected_face = None
        self.selected_faces.clear()

        mesh.selected_face = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.update()

        print(
            "LOOP CUT COMPLETE | Edges:",
            len(loop_edges),
            "| Faces Split:",
            cut_faces,
            "| Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True


    def bridge_selected_edge_loops(self):

        """
        Bridge two selected edge loops by creating quad faces between them.

        The current implementation works with two selected, connected edge
        components. Each component must form a closed loop or an open path,
        and both components must contain the same number of vertices.
        """

        # ---------------------------------
        # Validate editing state
        # ---------------------------------

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("BRIDGE: Requires EDIT mode")
                return False

        if not self.edge_mode:
            print("BRIDGE: Requires EDGE mode")
            return False

        if self.selected_object is None:
            print("BRIDGE: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("BRIDGE: Selected object has no mesh")
            return False

        # ---------------------------------
        # Read selected edges
        # ---------------------------------

        selected_edge_indices = sorted(
            int(index)
            for index in self.selected_edges
            if index is not None
        )

        if self.selected_edge is not None:
            if self.selected_edge not in selected_edge_indices:
                selected_edge_indices.append(
                    int(self.selected_edge)
                )
                selected_edge_indices.sort()

        valid_edges = []

        for edge_index in selected_edge_indices:

            if edge_index < 0 or edge_index >= len(mesh.edges):
                continue

            edge = mesh.edges[edge_index]

            if len(edge) != 2:
                continue

            valid_edges.append(
                (
                    int(edge[0]),
                    int(edge[1])
                )
            )

        if len(valid_edges) < 4:
            print("BRIDGE: Select two edge loops")
            return False

        # ---------------------------------
        # Build selected-edge graph
        # ---------------------------------

        adjacency = {}

        for a, b in valid_edges:
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)

        # Find connected components.
        components = []
        remaining = set(adjacency.keys())

        while remaining:

            start = next(iter(remaining))
            stack = [start]
            component = set()

            while stack:

                vertex = stack.pop()

                if vertex in component:
                    continue

                component.add(vertex)
                remaining.discard(vertex)

                for neighbor in adjacency.get(vertex, set()):
                    if neighbor not in component:
                        stack.append(neighbor)

            components.append(component)

        if len(components) != 2:
            print(
                "BRIDGE: Select exactly two connected edge loops"
            )
            return False

        # ---------------------------------
        # Order each selected component
        # ---------------------------------

        def order_component(component):

            local_adjacency = {
                vertex: [
                    neighbor
                    for neighbor in adjacency.get(vertex, set())
                    if neighbor in component
                ]
                for vertex in component
            }

            degrees = [
                len(neighbors)
                for neighbors in local_adjacency.values()
            ]

            if any(
                degree not in (1, 2)
                for degree in degrees
            ):
                return None

            # Closed loop: every vertex has degree two.
            closed = all(
                degree == 2
                for degree in degrees
            )

            if closed:
                start = min(component)
            else:
                endpoints = [
                    vertex
                    for vertex, neighbors
                    in local_adjacency.items()
                    if len(neighbors) == 1
                ]

                if len(endpoints) != 2:
                    return None

                start = min(endpoints)

            ordered = []
            previous = None
            current = start

            while True:

                ordered.append(current)

                neighbors = local_adjacency[current]

                candidates = [
                    neighbor
                    for neighbor in neighbors
                    if neighbor != previous
                ]

                if not candidates:
                    break

                next_vertex = candidates[0]

                if next_vertex == start:
                    break

                if next_vertex in ordered:
                    return None

                previous, current = current, next_vertex

                if len(ordered) > len(component):
                    return None

            if len(ordered) != len(component):
                return None

            return ordered, closed

        ordered_a = order_component(components[0])
        ordered_b = order_component(components[1])

        if ordered_a is None or ordered_b is None:
            print(
                "BRIDGE: Selected edges must form two valid loops or paths"
            )
            return False

        loop_a, closed_a = ordered_a
        loop_b, closed_b = ordered_b

        if len(loop_a) != len(loop_b):
            print(
                "BRIDGE: Both edge loops must have the same number of vertices"
            )
            return False

        if len(loop_a) < 2:
            print("BRIDGE: Edge loops are too small")
            return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:
            self.history_manager.save_state(
                self.selected_object
            )

        # ---------------------------------
        # Align loop direction and starting point
        # ---------------------------------

        positions_a = [
            np.array(mesh.vertices[index], dtype=np.float32)
            for index in loop_a
        ]

        positions_b = [
            np.array(mesh.vertices[index], dtype=np.float32)
            for index in loop_b
        ]

        count = len(loop_a)

        # For a closed loop, choose the cyclic shift and direction that
        # produces the smallest total distance between corresponding points.
        # For an open path, compare the forward and reversed orientations.
        candidates = []

        if closed_a and closed_b:

            for reverse in (False, True):

                base = list(reversed(loop_b)) if reverse else list(loop_b)

                for shift in range(count):

                    candidate = [
                        base[(index + shift) % count]
                        for index in range(count)
                    ]

                    distance = 0.0

                    for i in range(count):
                        va = positions_a[i]
                        vb = np.array(
                            mesh.vertices[candidate[i]],
                            dtype=np.float32
                        )
                        distance += float(
                            np.linalg.norm(va - vb)
                        )

                    candidates.append(
                        (distance, candidate)
                    )

        else:

            forward = list(loop_b)
            reverse = list(reversed(loop_b))

            for candidate in (forward, reverse):

                distance = 0.0

                for i in range(count):
                    va = positions_a[i]
                    vb = np.array(
                        mesh.vertices[candidate[i]],
                        dtype=np.float32
                    )
                    distance += float(
                        np.linalg.norm(va - vb)
                    )

                candidates.append(
                    (distance, candidate)
                )

        loop_b = min(
            candidates,
            key=lambda item: item[0]
        )[1]

        # ---------------------------------
        # Create bridge faces
        # ---------------------------------

        new_faces = []

        for i in range(count - 1):

            a0 = loop_a[i]
            a1 = loop_a[i + 1]
            b1 = loop_b[i + 1]
            b0 = loop_b[i]

            face = (
                a0,
                a1,
                b1,
                b0
            )

            if len(set(face)) == 4:
                new_faces.append(face)

        # Closed loops need the final wraparound face.
        if closed_a and closed_b:

            a0 = loop_a[-1]
            a1 = loop_a[0]
            b1 = loop_b[0]
            b0 = loop_b[-1]

            face = (
                a0,
                a1,
                b1,
                b0
            )

            if len(set(face)) == 4:
                new_faces.append(face)

        if not new_faces:
            print("BRIDGE: Could not create bridge faces")
            return False

        mesh.faces.extend(new_faces)
        mesh.build_edges()

        # ---------------------------------
        # Select the newly created bridge edges
        # ---------------------------------

        def canonical(edge):
            a, b = int(edge[0]), int(edge[1])
            return (a, b) if a < b else (b, a)

        bridge_edge_keys = set()

        for face in new_faces:
            for i in range(len(face)):
                bridge_edge_keys.add(
                    canonical((
                        face[i],
                        face[(i + 1) % len(face)]
                    ))
                )

        original_selected_keys = {
            canonical(edge)
            for edge in valid_edges
        }

        # Keep only the new cross-loop edges selected, not the original
        # boundary-loop edges.
        new_selected_edges = set()

        for edge_index, edge in enumerate(mesh.edges):

            key = canonical(edge)

            if (
                key in bridge_edge_keys
                and key not in original_selected_keys
            ):
                new_selected_edges.add(edge_index)

        self.selected_edges = new_selected_edges
        self.selected_edge = (
            next(iter(new_selected_edges))
            if new_selected_edges
            else None
        )

        self.selected_vertex = None
        self.selected_vertices.clear()
        self.selected_face = None
        self.selected_faces.clear()

        mesh.selected_face = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.update()

        print(
            "BRIDGE COMPLETE | Loops:",
            count,
            "vertices each | Faces Created:",
            len(new_faces),
            "| Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True


    def bevel_selected_edge(self, bevel_ratio=0.20):

        """
        Bevel the active selected edge.

        This implementation is intentionally limited to one manifold edge
        shared by exactly two quad faces. The selected edge is removed,
        four cut vertices are created on the four edges that leave the
        selected edge, and a new quad is created between the two faces.

        The two original faces are shortened so that they terminate at
        the new bevel face. The surrounding faces are split at the cut
        points and two corner triangles close the topology at the original
        edge endpoints.
        """

        # ---------------------------------
        # Validate editing state
        # ---------------------------------

        if self.main_window is not None:

            if self.main_window.mode_manager.get_mode() != "EDIT":

                print(
                    "BEVEL: Requires EDIT mode"
                )

                return False

        if not self.edge_mode:

            print(
                "BEVEL: Requires EDGE mode"
            )

            return False

        if self.selected_object is None:

            print(
                "BEVEL: No selected object"
            )

            return False

        mesh = self.selected_object.mesh

        if mesh is None:

            print(
                "BEVEL: Selected object has no mesh"
            )

            return False

        edge_index = self.selected_edge

        if edge_index is None:

            print(
                "BEVEL: No selected edge"
            )

            return False

        if (
            edge_index < 0
            or edge_index >= len(mesh.edges)
        ):

            print(
                "BEVEL: Invalid selected edge"
            )

            return False

        try:

            bevel_ratio = float(
                bevel_ratio
            )

        except (
            TypeError,
            ValueError
        ):

            print(
                "BEVEL: Invalid bevel amount"
            )

            return False

        if (
            bevel_ratio <= 0.0
            or bevel_ratio >= 0.5
        ):

            print(
                "BEVEL: Amount must be between 0 and 0.5"
            )

            return False

        # ---------------------------------
        # Helpers
        # ---------------------------------

        def canonical(edge):

            a = int(edge[0])
            b = int(edge[1])

            if a < b:
                return (
                    a,
                    b
                )

            return (
                b,
                a
            )

        def find_edge_in_face(face, target):

            count = len(face)

            for i in range(count):

                a = int(
                    face[i]
                )

                b = int(
                    face[(i + 1) % count]
                )

                if canonical((a, b)) == target:

                    return i

            return None

        selected_edge = tuple(
            int(index)
            for index in mesh.edges[edge_index]
        )

        if len(selected_edge) != 2:

            print(
                "BEVEL: Invalid edge data"
            )

            return False

        vertex_a = selected_edge[0]
        vertex_b = selected_edge[1]

        target_edge = canonical(
            (
                vertex_a,
                vertex_b
            )
        )

        # ---------------------------------
        # Snapshot original topology
        # ---------------------------------

        original_faces = [
            tuple(
                int(index)
                for index in face
            )
            for face in mesh.faces
            if face is not None
        ]

        if not original_faces:

            print(
                "BEVEL: Mesh has no faces"
            )

            return False

        # ---------------------------------
        # Find the two faces sharing the
        # selected edge.
        # ---------------------------------

        incident_faces = []

        for face_index, face in enumerate(
            original_faces
        ):

            if len(face) != 4:
                continue

            if find_edge_in_face(
                face,
                target_edge
            ) is not None:

                incident_faces.append(
                    face_index
                )

        if len(incident_faces) != 2:

            print(
                "BEVEL: Selected edge must have exactly two quad faces"
            )

            return False

        # ---------------------------------
        # Determine the two edges leaving
        # each endpoint of the selected edge
        # on each incident face.
        # ---------------------------------

        face_data = {}

        affected_edges = set()

        for face_index in incident_faces:

            face = original_faces[
                face_index
            ]

            edge_position = find_edge_in_face(
                face,
                target_edge
            )

            if edge_position is None:

                print(
                    "BEVEL: Could not determine selected edge position"
                )

                return False

            x = int(
                face[edge_position]
            )

            y = int(
                face[
                    (edge_position + 1) % 4
                ]
            )

            # Normalize the selected edge to A -> B
            # while preserving the face's winding.
            if (
                x == vertex_a
                and y == vertex_b
            ):

                neighbor_a = int(
                    face[
                        (edge_position - 1) % 4
                    ]
                )

                neighbor_b = int(
                    face[
                        (edge_position + 2) % 4
                    ]
                )

                orientation = "AB"

            elif (
                x == vertex_b
                and y == vertex_a
            ):

                neighbor_b = int(
                    face[
                        (edge_position - 1) % 4
                    ]
                )

                neighbor_a = int(
                    face[
                        (edge_position + 2) % 4
                    ]
                )

                orientation = "BA"

            else:

                print(
                    "BEVEL: Invalid selected edge topology"
                )

                return False

            edge_from_a = canonical(
                (
                    vertex_a,
                    neighbor_a
                )
            )

            edge_from_b = canonical(
                (
                    vertex_b,
                    neighbor_b
                )
            )

            if (
                edge_from_a == target_edge
                or edge_from_b == target_edge
            ):

                print(
                    "BEVEL: Invalid adjacent topology"
                )

                return False

            face_data[
                face_index
            ] = {
                "neighbor_a": neighbor_a,
                "neighbor_b": neighbor_b,
                "orientation": orientation,
                "edge_from_a": edge_from_a,
                "edge_from_b": edge_from_b
            }

            affected_edges.add(
                edge_from_a
            )

            affected_edges.add(
                edge_from_b
            )

        # A proper single-edge bevel needs four different outgoing edges.
        if len(affected_edges) != 4:

            print(
                "BEVEL: Selected edge does not have four valid adjacent edges"
            )

            return False

        # ---------------------------------
        # Validate all affected edges.
        # ---------------------------------

        for edge in affected_edges:

            a, b = edge

            if (
                a < 0
                or b < 0
                or a >= len(mesh.vertices)
                or b >= len(mesh.vertices)
            ):

                print(
                    "BEVEL: Invalid adjacent vertex"
                )

                return False

            if not any(
                canonical(
                    (
                        face[i],
                        face[
                            (i + 1) % len(face)
                        ]
                    )
                ) == edge
                for face in original_faces
                for i in range(len(face))
            ):

                print(
                    "BEVEL: Adjacent edge is not part of the mesh"
                )

                return False

        # ---------------------------------
        # Save undo state only after every
        # topology validation has succeeded.
        # ---------------------------------

        if self.history_manager is not None:

            self.history_manager.save_state(
                self.selected_object
            )

        # ---------------------------------
        # Create the four cut vertices.
        #
        # Each cut point is keyed by the
        # actual edge being shortened.
        # ---------------------------------

        split_points = {}

        for edge in sorted(
            affected_edges
        ):

            a, b = edge

            va = np.array(
                mesh.vertices[a],
                dtype=np.float32
            )

            vb = np.array(
                mesh.vertices[b],
                dtype=np.float32
            )

            # Determine which endpoint of the
            # selected edge this adjacent edge
            # belongs to.
            if vertex_a in edge:

                start = np.array(
                    mesh.vertices[
                        vertex_a
                    ],
                    dtype=np.float32
                )

                other_index = (
                    b
                    if a == vertex_a
                    else a
                )

            elif vertex_b in edge:

                start = np.array(
                    mesh.vertices[
                        vertex_b
                    ],
                    dtype=np.float32
                )

                other_index = (
                    b
                    if a == vertex_b
                    else a
                )

            else:

                print(
                    "BEVEL: Adjacent edge has no selected-edge endpoint"
                )

                return False

            other = np.array(
                mesh.vertices[
                    other_index
                ],
                dtype=np.float32
            )

            cut_point = (
                start
                + (
                    other - start
                ) * bevel_ratio
            )

            mesh.vertices.append(
                [
                    float(cut_point[0]),
                    float(cut_point[1]),
                    float(cut_point[2])
                ]
            )

            split_points[
                edge
            ] = len(
                mesh.vertices
            ) - 1

        # ---------------------------------
        # Rebuild faces.
        #
        # The two incident faces become
        # shortened faces. Every other face
        # crossing a cut edge gets that edge
        # split at the new vertex.
        # ---------------------------------

        new_faces = []

        incident_set = set(
            incident_faces
        )

        for face_index, face in enumerate(
            original_faces
        ):

            # ---------------------------------
            # The two faces touching the
            # selected edge are shortened.
            # ---------------------------------

            if face_index in incident_set:

                data = face_data[
                    face_index
                ]

                cut_a = split_points[
                    data["edge_from_a"]
                ]

                cut_b = split_points[
                    data["edge_from_b"]
                ]

                neighbor_a = data[
                    "neighbor_a"
                ]

                neighbor_b = data[
                    "neighbor_b"
                ]

                if data[
                    "orientation"
                ] == "AB":

                    shortened_face = (
                        cut_a,
                        cut_b,
                        neighbor_b,
                        neighbor_a
                    )

                else:

                    shortened_face = (
                        cut_b,
                        cut_a,
                        neighbor_a,
                        neighbor_b
                    )

                new_faces.append(
                    shortened_face
                )

                continue

            # ---------------------------------
            # All other faces keep their
            # topology but receive the new
            # cut vertex wherever one of
            # their edges was shortened.
            # ---------------------------------

            rebuilt_face = []

            count = len(
                face
            )

            for i in range(count):

                current = int(
                    face[i]
                )

                next_vertex = int(
                    face[
                        (i + 1) % count
                    ]
                )

                rebuilt_face.append(
                    current
                )

                split_index = split_points.get(
                    canonical(
                        (
                            current,
                            next_vertex
                        )
                    )
                )

                if split_index is not None:

                    rebuilt_face.append(
                        split_index
                    )

            # Avoid accidentally keeping a
            # degenerate face.
            if len(
                set(rebuilt_face)
            ) >= 3:

                new_faces.append(
                    tuple(
                        rebuilt_face
                    )
                )

        # ---------------------------------
        # Create the new bevel face.
        #
        # It connects the cut point on the
        # first incident face to the cut
        # point on the second incident face.
        # ---------------------------------

        first_data = face_data[
            incident_faces[0]
        ]

        second_data = face_data[
            incident_faces[1]
        ]

        first_cut_a = split_points[
            first_data[
                "edge_from_a"
            ]
        ]

        first_cut_b = split_points[
            first_data[
                "edge_from_b"
            ]
        ]

        second_cut_a = split_points[
            second_data[
                "edge_from_a"
            ]
        ]

        second_cut_b = split_points[
            second_data[
                "edge_from_b"
            ]
        ]

        if first_data[
            "orientation"
        ] == "AB":

            bevel_face = (
                first_cut_a,
                first_cut_b,
                second_cut_b,
                second_cut_a
            )

        else:

            bevel_face = (
                first_cut_b,
                first_cut_a,
                second_cut_a,
                second_cut_b
            )

        new_faces.append(
            bevel_face
        )

        # ---------------------------------
        # Close the two original corners.
        #
        # These triangles attach the two
        # side faces to the new bevel surface
        # instead of leaving an open corner.
        # ---------------------------------

        corner_a = (
            vertex_a,
            first_cut_a,
            second_cut_a
        )

        corner_b = (
            vertex_b,
            second_cut_b,
            first_cut_b
        )

        new_faces.append(
            corner_a
        )

        new_faces.append(
            corner_b
        )

        # ---------------------------------
        # Commit the rebuilt topology.
        # ---------------------------------

        mesh.faces = new_faces

        mesh.build_edges()

        # ---------------------------------
        # Select the new bevel edge.
        # ---------------------------------

        bevel_edge_key = canonical(
            (
                first_cut_a,
                first_cut_b
            )
        )

        self.selected_edge = None
        self.selected_edges.clear()

        for new_edge_index, edge in enumerate(
            mesh.edges
        ):

            if canonical(
                edge
            ) == bevel_edge_key:

                self.selected_edge = (
                    new_edge_index
                )

                self.selected_edges.add(
                    new_edge_index
                )

                break

        # ---------------------------------
        # Clear incompatible edit selections.
        # ---------------------------------

        self.selected_vertex = None
        self.selected_vertices.clear()

        self.selected_face = None
        self.selected_faces.clear()

        mesh.selected_face = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False
        self.dragging_object = False

        self.update()

        print(
            "BEVEL COMPLETE | Edge:",
            edge_index,
            "| Ratio:",
            bevel_ratio,
            "| Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True
    def merge_selected_vertices(self):
        """
        Merge all currently selected vertices into their average position.

        The selected vertices are replaced by one vertex. Face references are
        redirected to that vertex, degenerate faces are removed, unused
        vertices are compacted, and the derived edge list is rebuilt.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("MERGE: Requires EDIT mode")
                return False

        if not self.vertex_mode:
            print("MERGE: Requires VERTEX mode")
            return False

        if self.selected_object is None:
            print("MERGE: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("MERGE: Selected object has no mesh")
            return False

        selected = sorted(
            int(index)
            for index in self.selected_vertices
            if index is not None
        )

        selected = [
            index
            for index in selected
            if 0 <= index < len(mesh.vertices)
        ]

        selected = sorted(set(selected))

        # Support the single selected vertex state as well.
        if self.selected_vertex is not None:
            if 0 <= self.selected_vertex < len(mesh.vertices):
                if self.selected_vertex not in selected:
                    selected.append(
                        int(self.selected_vertex)
                    )
                    selected.sort()

        if len(selected) < 2:
            print("MERGE: Select at least two vertices")
            return False

        # ---------------------------------
        # Save undo state
        # ---------------------------------

        if self.history_manager is not None:
            self.history_manager.save_state(
                self.selected_object
            )

        # ---------------------------------
        # Calculate merge position
        # ---------------------------------

        positions = np.array(
            [mesh.vertices[index] for index in selected],
            dtype=np.float32
        )

        merged_position = np.mean(
            positions,
            axis=0
        )

        target_vertex = selected[0]
        selected_set = set(selected)

        mesh.vertices[target_vertex] = [
            float(merged_position[0]),
            float(merged_position[1]),
            float(merged_position[2])
        ]

        # ---------------------------------
        # Redirect faces to the merge vertex
        # ---------------------------------

        merged_faces = []

        for face in mesh.faces:

            if face is None:
                continue

            redirected = []

            for vertex_index in face:

                vertex_index = int(vertex_index)

                if vertex_index in selected_set:
                    vertex_index = target_vertex

                # Remove repeated consecutive indices immediately.
                if not redirected or redirected[-1] != vertex_index:
                    redirected.append(vertex_index)

            # Remove a repeated closing index.
            if (
                len(redirected) > 1
                and redirected[0] == redirected[-1]
            ):
                redirected.pop()

            if len(redirected) < 3:
                continue

            if len(set(redirected)) < 3:
                continue

            merged_faces.append(
                tuple(redirected)
            )

        mesh.faces = merged_faces

        # ---------------------------------
        # Remove duplicate faces created by the merge
        # ---------------------------------

        unique_faces = []
        seen_faces = set()

        for face in mesh.faces:

            # Face winding is retained. Only exact duplicate faces are
            # removed here so normal/orientation information is preserved.
            key = tuple(face)

            if key in seen_faces:
                continue

            seen_faces.add(key)
            unique_faces.append(face)

        mesh.faces = unique_faces

        # ---------------------------------
        # Compact unused vertices and rebuild topology
        # ---------------------------------

        used_vertices = set()

        for face in mesh.faces:
            for vertex_index in face:
                used_vertices.add(
                    int(vertex_index)
                )

        vertex_remap = {}
        new_vertices = []

        for old_index, vertex in enumerate(mesh.vertices):

            if old_index not in used_vertices:
                continue

            vertex_remap[old_index] = len(
                new_vertices
            )

            new_vertices.append([
                float(vertex[0]),
                float(vertex[1]),
                float(vertex[2])
            ])

        remapped_faces = []

        for face in mesh.faces:

            remapped = []
            valid = True

            for vertex_index in face:

                if vertex_index not in vertex_remap:
                    valid = False
                    break

                remapped.append(
                    vertex_remap[vertex_index]
                )

            if not valid:
                continue

            if len(remapped) < 3:
                continue

            if len(set(remapped)) < 3:
                continue

            remapped_faces.append(
                tuple(remapped)
            )

        mesh.vertices = new_vertices
        mesh.faces = remapped_faces
        mesh.build_edges()

        # ---------------------------------
        # Restore selection on merged vertex
        # ---------------------------------

        new_target = vertex_remap.get(
            target_vertex
        )

        self.selected_vertices.clear()
        self.selected_vertex = new_target

        if new_target is not None:
            self.selected_vertices.add(
                new_target
            )

        self.selected_edge = None
        self.selected_edges.clear()
        self.selected_face = None
        self.selected_faces.clear()

        mesh.selected_vertex = new_target
        mesh.selected_edge = None
        mesh.selected_face = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False

        self.update()

        print(
            "MERGE COMPLETE | Merged:",
            len(selected),
            "vertices | Remaining Vertices:",
            len(mesh.vertices),
            "| Faces:",
            len(mesh.faces),
            "| Edges:",
            len(mesh.edges)
        )

        return True



    def connect_selected_vertices(self):
        """Connect exactly two selected vertices by splitting shared faces."""

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("CONNECT: Requires EDIT mode")
                return False

        if not self.vertex_mode:
            print("CONNECT: Requires VERTEX mode")
            return False

        if self.selected_object is None or self.selected_object.mesh is None:
            print("CONNECT: No selected mesh")
            return False

        mesh = self.selected_object.mesh

        selected = set()
        for index in self.selected_vertices:
            try:
                index = int(index)
            except (TypeError, ValueError):
                continue
            if 0 <= index < len(mesh.vertices):
                selected.add(index)

        if self.selected_vertex is not None:
            try:
                index = int(self.selected_vertex)
                if 0 <= index < len(mesh.vertices):
                    selected.add(index)
            except (TypeError, ValueError):
                pass

        if len(selected) != 2:
            print("CONNECT: Select exactly two vertices")
            return False

        vertex_a, vertex_b = sorted(selected)

        # Do not create a duplicate edge.
        existing_edge = False
        for edge in mesh.edges:
            if len(edge) != 2:
                continue
            if set((int(edge[0]), int(edge[1]))) == {vertex_a, vertex_b}:
                existing_edge = True
                break

        if existing_edge:
            print("CONNECT: Vertices are already connected")
            return False

        # The two vertices must share at least one face. Connecting vertices
        # from unrelated faces would create a loose edge rather than topology.
        new_faces = []
        split_count = 0

        for face in mesh.faces:
            face_vertices = [int(index) for index in face]

            if vertex_a not in face_vertices or vertex_b not in face_vertices:
                new_faces.append(tuple(face_vertices))
                continue

            position_a = face_vertices.index(vertex_a)
            position_b = face_vertices.index(vertex_b)

            if position_a == position_b:
                new_faces.append(tuple(face_vertices))
                continue

            # If the vertices are already adjacent in this face, the edge
            # exists topologically even if the derived edge list is stale.
            if (
                (position_a + 1) % len(face_vertices) == position_b
                or
                (position_b + 1) % len(face_vertices) == position_a
            ):
                new_faces.append(tuple(face_vertices))
                continue

            # Walk from A to B in the face's existing winding.
            path_ab = []
            current = position_a
            while True:
                path_ab.append(face_vertices[current])
                if current == position_b:
                    break
                current = (current + 1) % len(face_vertices)

            # Walk from B back to A in the same winding.
            path_ba = []
            current = position_b
            while True:
                path_ba.append(face_vertices[current])
                if current == position_a:
                    break
                current = (current + 1) % len(face_vertices)

            if len(path_ab) >= 3 and len(path_ba) >= 3:
                new_faces.append(tuple(path_ab))
                new_faces.append(tuple(path_ba))
                split_count += 1
            else:
                new_faces.append(tuple(face_vertices))

        if split_count == 0:
            print("CONNECT: Vertices must be non-adjacent on a common face")
            return False

        if self.history_manager is not None:
            self.history_manager.save_state(self.selected_object)

        mesh.faces = new_faces
        mesh.build_edges()

        # Keep the two vertices selected after the connection.
        self.selected_vertices = {vertex_a, vertex_b}
        self.selected_vertex = vertex_a

        self.selected_edges.clear()
        self.selected_edge = None
        self.selected_faces.clear()
        self.selected_face = None

        mesh.selected_vertex = vertex_a
        mesh.selected_edge = None
        mesh.selected_face = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False
        self.loop_cut_dragging = False

        self.update()

        print(
            "CONNECT COMPLETE | Vertices:",
            vertex_a,
            vertex_b,
            "| Faces split:",
            split_count
        )
        return True


    def split_selected_edit_element(self):
        """
        Split selected Edit Mode geometry by disconnecting its topology.

        Vertex Mode:
            The selected vertex is duplicated for every additional incident
            face, leaving the first incident face on the original vertex.

        Edge Mode:
            The selected edge is disconnected from every additional incident
            face by duplicating its two endpoints.

        Face Mode:
            The selected face receives its own copy of every vertex, making
            that face independently movable without pulling its neighbors.
        """

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("SPLIT: Requires EDIT mode")
                return False

        if self.selected_object is None:
            print("SPLIT: No selected object")
            return False

        mesh = self.selected_object.mesh

        if mesh is None:
            print("SPLIT: Selected object has no mesh")
            return False

        # ------------------------------------------------------------
        # Resolve the active selection before touching the mesh.
        # ------------------------------------------------------------

        mode = None
        selected = set()

        if self.vertex_mode:
            mode = "VERTEX"
            selected = {
                int(index)
                for index in self.selected_vertices
                if isinstance(index, (int, float))
                and 0 <= int(index) < len(mesh.vertices)
            }

            if self.selected_vertex is not None:
                try:
                    index = int(self.selected_vertex)
                    if 0 <= index < len(mesh.vertices):
                        selected.add(index)
                except (TypeError, ValueError):
                    pass

        elif self.edge_mode:
            mode = "EDGE"
            selected = {
                int(index)
                for index in self.selected_edges
                if isinstance(index, (int, float))
                and 0 <= int(index) < len(mesh.edges)
            }

            if self.selected_edge is not None:
                try:
                    index = int(self.selected_edge)
                    if 0 <= index < len(mesh.edges):
                        selected.add(index)
                except (TypeError, ValueError):
                    pass

        elif self.face_mode:
            mode = "FACE"
            selected = {
                int(index)
                for index in self.selected_faces
                if isinstance(index, (int, float))
                and 0 <= int(index) < len(mesh.faces)
                and len(mesh.faces[int(index)]) >= 3
            }

            if self.selected_face is not None:
                try:
                    index = int(self.selected_face)
                    if (
                        0 <= index < len(mesh.faces)
                        and len(mesh.faces[index]) >= 3
                    ):
                        selected.add(index)
                except (TypeError, ValueError):
                    pass

        if mode is None:
            print("SPLIT: No active selection mode")
            return False

        if not selected:
            print("SPLIT: Nothing selected")
            return False

        # ------------------------------------------------------------
        # Save a small rollback copy. This prevents a failed split from
        # leaving the mesh partially modified.
        # ------------------------------------------------------------

        old_vertices = [
            list(vertex)
            for vertex in mesh.vertices
        ]

        old_faces = [
            tuple(face)
            for face in mesh.faces
        ]

        old_edges = [
            tuple(edge)
            for edge in mesh.edges
        ]

        try:

            # --------------------------------------------------------
            # Save the normal undo state only after selection validation.
            # --------------------------------------------------------

            if self.history_manager is not None:
                self.history_manager.save_state(
                    self.selected_object
                )

            changed = False

            # ========================================================
            # VERTEX SPLIT
            # ========================================================

            if mode == "VERTEX":

                for vertex_index in sorted(selected):

                    incident_faces = [
                        face_index
                        for face_index, face in enumerate(mesh.faces)
                        if vertex_index in face
                    ]

                    if len(incident_faces) <= 1:
                        continue

                    # The first face keeps the original vertex.
                    for face_index in incident_faces[1:]:

                        new_vertex_index = len(mesh.vertices)

                        mesh.vertices.append(
                            [
                                float(mesh.vertices[vertex_index][0]),
                                float(mesh.vertices[vertex_index][1]),
                                float(mesh.vertices[vertex_index][2])
                            ]
                        )

                        mesh.faces[face_index] = tuple(
                            new_vertex_index
                            if int(vertex) == vertex_index
                            else int(vertex)
                            for vertex in mesh.faces[face_index]
                        )

                        changed = True

                if not changed:
                    print(
                        "SPLIT: Vertex is already disconnected"
                    )
                    return False

                print("SPLIT: Vertex separated")

            # ========================================================
            # EDGE SPLIT
            # ========================================================

            elif mode == "EDGE":

                for edge_index in sorted(selected):

                    if (
                        edge_index < 0
                        or edge_index >= len(mesh.edges)
                    ):
                        continue

                    edge = mesh.edges[edge_index]

                    if len(edge) != 2:
                        continue

                    vertex_a = int(edge[0])
                    vertex_b = int(edge[1])

                    target = {
                        vertex_a,
                        vertex_b
                    }

                    incident_faces = []

                    for face_index, face in enumerate(mesh.faces):

                        face_vertices = [
                            int(vertex)
                            for vertex in face
                        ]

                        for i in range(
                            len(face_vertices)
                        ):

                            a = face_vertices[i]
                            b = face_vertices[
                                (i + 1) % len(face_vertices)
                            ]

                            if {a, b} == target:
                                incident_faces.append(
                                    face_index
                                )
                                break

                    if len(incident_faces) <= 1:
                        continue

                    # The first incident face keeps the original edge.
                    for face_index in incident_faces[1:]:

                        new_a = len(mesh.vertices)

                        mesh.vertices.append(
                            [
                                float(mesh.vertices[vertex_a][0]),
                                float(mesh.vertices[vertex_a][1]),
                                float(mesh.vertices[vertex_a][2])
                            ]
                        )

                        new_b = len(mesh.vertices)

                        mesh.vertices.append(
                            [
                                float(mesh.vertices[vertex_b][0]),
                                float(mesh.vertices[vertex_b][1]),
                                float(mesh.vertices[vertex_b][2])
                            ]
                        )

                        mesh.faces[face_index] = tuple(
                            new_a
                            if int(vertex) == vertex_a
                            else new_b
                            if int(vertex) == vertex_b
                            else int(vertex)
                            for vertex in mesh.faces[face_index]
                        )

                        changed = True

                if not changed:
                    print(
                        "SPLIT: Edge is already disconnected"
                    )
                    return False

                print("SPLIT: Edge separated")

            # ========================================================
            # FACE SPLIT
            # ========================================================

            elif mode == "FACE":

                for face_index in sorted(selected):

                    original_face = tuple(
                        int(vertex)
                        for vertex in mesh.faces[face_index]
                    )

                    if len(original_face) < 3:
                        continue

                    remap = {}

                    for vertex_index in original_face:

                        if vertex_index in remap:
                            continue

                        new_vertex_index = len(mesh.vertices)

                        mesh.vertices.append(
                            [
                                float(mesh.vertices[vertex_index][0]),
                                float(mesh.vertices[vertex_index][1]),
                                float(mesh.vertices[vertex_index][2])
                            ]
                        )

                        remap[vertex_index] = (
                            new_vertex_index
                        )

                    mesh.faces[face_index] = tuple(
                        remap[vertex]
                        for vertex in original_face
                    )

                    changed = True

                if not changed:
                    print(
                        "SPLIT: Face could not be separated"
                    )
                    return False

                print("SPLIT: Face separated")

            # --------------------------------------------------------
            # Validate topology before rebuilding derived edges.
            # --------------------------------------------------------

            for face in mesh.faces:

                if face is None:
                    raise ValueError(
                        "SPLIT created an invalid face"
                    )

                if len(face) < 3:
                    raise ValueError(
                        "SPLIT created a degenerate face"
                    )

                if len(set(int(v) for v in face)) < 3:
                    raise ValueError(
                        "SPLIT created repeated face vertices"
                    )

                for vertex_index in face:

                    if (
                        int(vertex_index) < 0
                        or int(vertex_index) >= len(mesh.vertices)
                    ):
                        raise ValueError(
                            "SPLIT created an invalid vertex reference"
                        )

            # --------------------------------------------------------
            # Rebuild derived topology.
            # --------------------------------------------------------

            mesh.build_edges()

            # --------------------------------------------------------
            # Keep the original selection mode and valid selection.
            # Face selection is especially important here because the
            # selected face should be movable after splitting.
            # --------------------------------------------------------

            if mode == "FACE":

                self.selected_faces = set(selected)

                if self.selected_face is not None:
                    self.selected_face = int(
                        self.selected_face
                    )
                else:
                    self.selected_face = min(selected)

                mesh.selected_face = (
                    self.selected_face
                )

            elif mode == "VERTEX":

                self.selected_vertices = set(selected)

                if self.selected_vertex is not None:
                    self.selected_vertex = int(
                        self.selected_vertex
                    )

                mesh.selected_vertex = (
                    self.selected_vertex
                )

            elif mode == "EDGE":

                # Rebuild the selected edge index from its endpoint pair
                # because mesh.build_edges() may reorder derived edges.
                self.selected_edges.clear()
                self.selected_edge = None

            self.vertex_dragging = False
            self.edge_dragging = False
            self.face_dragging = False
            self.loop_cut_dragging = False

            self.update()

            print(
                "SPLIT COMPLETE | Mode:",
                mode,
                "| Vertices:",
                len(mesh.vertices),
                "| Faces:",
                len(mesh.faces),
                "| Edges:",
                len(mesh.edges)
            )

            return True

        except Exception as error:

            # --------------------------------------------------------
            # Roll back every mesh mutation if anything fails.
            # --------------------------------------------------------

            mesh.vertices = old_vertices
            mesh.faces = old_faces
            mesh.edges = old_edges

            print(
                "SPLIT FAILED - MESH RESTORED:",
                repr(error)
            )

            self.update()

            return False

    def fill_selected_boundary(self):
        """Fill one selected closed boundary edge loop with a new face."""

        if self.main_window is not None:
            if self.main_window.mode_manager.get_mode() != "EDIT":
                print("FILL: Requires EDIT mode")
                return False

        if not self.edge_mode:
            print("FILL: Requires EDGE mode")
            return False

        if self.selected_object is None or self.selected_object.mesh is None:
            print("FILL: No selected mesh")
            return False

        mesh = self.selected_object.mesh
        selected = set(self.selected_edges)

        if self.selected_edge is not None:
            selected.add(self.selected_edge)

        selected = {
            int(index) for index in selected
            if 0 <= int(index) < len(mesh.edges)
        }

        if len(selected) < 3:
            print("FILL: Select a closed boundary edge loop")
            return False

        # Build an undirected graph from the selected edges.
        adjacency = {}
        edge_pairs = []

        for edge_index in selected:
            edge = mesh.edges[edge_index]
            if len(edge) != 2:
                print("FILL: Invalid edge")
                return False

            a = int(edge[0])
            b = int(edge[1])

            if a == b:
                print("FILL: Degenerate edge")
                return False

            if a < 0 or b < 0 or a >= len(mesh.vertices) or b >= len(mesh.vertices):
                print("FILL: Invalid vertex index")
                return False

            adjacency.setdefault(a, []).append(b)
            adjacency.setdefault(b, []).append(a)
            edge_pairs.append((a, b))

        # A closed loop has exactly two selected neighbors at every vertex.
        if any(len(neighbors) != 2 for neighbors in adjacency.values()):
            print("FILL: Selected edges must form one closed loop")
            return False

        # Follow the loop in edge order.
        start = next(iter(adjacency))
        ordered = [start]
        previous = None
        current = start

        while True:
            neighbors = adjacency[current]
            if previous is None:
                next_vertex = neighbors[0]
            else:
                next_vertex = neighbors[0] if neighbors[0] != previous else neighbors[1]

            if next_vertex == start:
                break

            if next_vertex in ordered:
                print("FILL: Selected edges do not form one simple loop")
                return False

            ordered.append(next_vertex)
            previous, current = current, next_vertex

            if len(ordered) > len(adjacency):
                print("FILL: Invalid loop")
                return False

        if len(ordered) != len(adjacency) or len(ordered) < 3:
            print("FILL: Selected edges must form one closed loop")
            return False

        # Confirm every selected edge belongs to the discovered loop.
        loop_edges = set()
        for i, vertex_a in enumerate(ordered):
            vertex_b = ordered[(i + 1) % len(ordered)]
            loop_edges.add(frozenset((vertex_a, vertex_b)))

        selected_edge_pairs = {
            frozenset(pair) for pair in edge_pairs
        }
        if loop_edges != selected_edge_pairs:
            print("FILL: Selected edges must form one closed loop")
            return False

        # Reject loops that are already completely bounded by an existing face.
        ordered_edge_set = set(loop_edges)
        for face in mesh.faces:
            if len(face) != len(ordered):
                continue
            face_edges = set()
            for i, vertex_a in enumerate(face):
                vertex_b = face[(i + 1) % len(face)]
                face_edges.add(frozenset((vertex_a, vertex_b)))
            if face_edges == ordered_edge_set:
                print("FILL: Boundary already has a face")
                return False

        if self.history_manager is not None:
            self.history_manager.save_state(self.selected_object)

        # Use the selected loop order as the polygon winding.
        new_face = tuple(ordered)
        mesh.faces.append(new_face)
        new_face_index = len(mesh.faces) - 1
        mesh.build_edges()

        self.selected_faces = {new_face_index}
        self.selected_face = new_face_index
        self.selected_edges.clear()
        self.selected_edge = None
        self.selected_vertices.clear()
        self.selected_vertex = None

        mesh.selected_face = new_face_index
        mesh.selected_edge = None
        mesh.selected_vertex = None

        self.vertex_dragging = False
        self.edge_dragging = False
        self.face_dragging = False
        self.loop_cut_dragging = False

        self.update()

        print(
            "FILL COMPLETE | Face:",
            new_face_index,
            "| Vertices:",
            ordered
        )
        return True

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

            # X in Vertex Mode performs a vertex dissolve, preserving the
            # surrounding surface. Delete keeps the existing destructive
            # vertex deletion behavior.
            if (
                event.key() == Qt.Key_X
                and self.main_window.mode_manager.get_mode()
                == "EDIT"
                and self.vertex_mode
            ):

                print("DISSOLVE VERTEX")

                self.dissolve_selected_vertex()

                return

            if (
                event.key() == Qt.Key_X
                and self.main_window.mode_manager.get_mode()
                == "EDIT"
                and self.edge_mode
            ):

                print("DISSOLVE EDGE")

                self.dissolve_selected_edge()

                return

            if (
                event.key() == Qt.Key_X
                and self.main_window.mode_manager.get_mode()
                == "EDIT"
                and self.face_mode
            ):

                print("DISSOLVE FACE")

                self.dissolve_selected_face()

                return

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
        # LOOP CUT
        # ---------------------------------
        elif (
            event.key() == Qt.Key_R
            and event.modifiers() & Qt.ControlModifier
        ):

            print("LOOP CUT")

            self.loop_cut_selected_edge()

            return

        # ---------------------------------
        # BEVEL
        # ---------------------------------
        elif (
            event.key() == Qt.Key_B
            and event.modifiers() & Qt.ControlModifier
        ):

            print("BEVEL")

            self.bevel_selected_edge()

            return

        # ---------------------------------
        # BRIDGE EDGE LOOPS
        # ---------------------------------
        elif (
            event.key() == Qt.Key_E
            and event.modifiers() & Qt.ControlModifier
        ):

            print("BRIDGE EDGE LOOPS")

            self.bridge_selected_edge_loops()

            return

        # ---------------------------------
        # MERGE / WELD VERTICES
        # ---------------------------------
        elif event.key() == Qt.Key_M:

            print("MERGE VERTICES")

            self.merge_selected_vertices()

            return

        # ---------------------------------
        # CONNECT VERTICES
        # ---------------------------------
        elif event.key() == Qt.Key_J:

            print("CONNECT VERTICES")

            self.connect_selected_vertices()

            return

        # ---------------------------------
        # SPLIT
        # ---------------------------------
        elif event.key() == Qt.Key_Y:

            print("SPLIT")

            self.split_selected_edit_element()

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
        # FILL
        # ---------------------------------
        elif event.key() == Qt.Key_F:

            print("FILL")

            self.fill_selected_boundary()

            return

        # ---------------------------------
        # INSET
        # ---------------------------------
        elif event.key() == Qt.Key_I:

            print("INSET")

            self.inset_selected_face(
                0.20
            )

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

        threshold = 0.18

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

