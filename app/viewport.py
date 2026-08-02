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

class Viewport(QOpenGLWidget):

    def __init__(self, main_window = None):
        super().__init__()

        self.main_window = main_window

        self.webcam_frame = None

        self.webcam_texture = None

        self.camera = Camera()

        self.scene_objects = []

        self.cursor_x = 0.0
        self.cursor_y = 0.0

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        self.last_mouse_x = 0

        self.last_mouse_y = 0

        self.right_mouse = False

        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.mouse_pressed = False

        self.selection_manager = SelectionManager(self)

        self.selected_vertex = None

        self.selected_edge = None

        self.edge_dragging = False

        self.raycaster = RayCaster()

        self.mouse_x = 0
        self.mouse_y = 0

        self.dragging_object = False

        self.drag_start_x = 0
        self.drag_start_y = 0

        self.move_gizmo = MoveGizmo()

        self.drag_plane_y = 0.0
        self.drag_offset = None

        self.rotate_gizmo = RotateGizmo()

        self.scale_gizmo = ScaleGizmo()

        self.tool_manager = ToolManager()

        self.vertex_dragging = False

        self.vertex_drag_start = None

        self.vertex_original = None

        self.edge_dragging = False

        self.edge_vertex_a = None
        self.edge_vertex_b = None

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        print("Viewport Focus:", self.hasFocus())

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

                MeshRenderer.draw(obj.mesh)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edge
                    )

                    self.draw_vertices(obj.mesh)

            else:

                self.draw_cube()

        elif obj.object_type == "Sphere":

             if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edge
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Plane":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edge
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Cylinder":

             if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edge
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Cone":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edge
                    )

                    self.draw_vertices(obj.mesh)

        elif obj.object_type == "Torus":

            if obj.mesh is not None:

                MeshRenderer.draw(obj.mesh)

                if (
                    obj == self.selected_object
                    and self.main_window.mode_manager.get_mode() == "EDIT"
                ):

                    MeshRenderer.draw_edges(
                        obj.mesh,
                        self.selected_edge
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

        glPushAttrib(GL_ENABLE_BIT | GL_POINT_BIT | GL_CURRENT_BIT)

        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)

        glPointSize(8)

        glColor3f(1.0, 0.3, 0.0)

        glBegin(GL_POINTS)

        for i, vertex in enumerate(mesh.vertices):

            glVertex3f(
                vertex[0],
                vertex[1],
                vertex[2]
            )

        glEnd()

        # Draw selected vertex separately so it can have a larger size
        if (
            hasattr(self, "selected_vertex")
            and self.selected_vertex is not None
            and 0 <= self.selected_vertex < len(mesh.vertices)
        ):

            vertex = mesh.vertices[self.selected_vertex]

            glPointSize(12)

            glColor3f(1.0, 1.0, 0.0)

            glBegin(GL_POINTS)

            glVertex3f(
                vertex[0],
                vertex[1],
                vertex[2]
            )

            glEnd()

        glEnable(GL_TEXTURE_2D)

        glPopAttrib()

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

            self.selected_manager.select(closest)

            print(
                "SELECTED:",
                closest.name
            )

            self.update()
        else:

            self.selected_manager.deselect()

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
            # EDIT MODE (Vertex Selection)
            # -------------------------------------------------

            if self.main_window.mode_manager.get_mode() == "EDIT":

                obj = self.selected_object

                if obj is not None:

                    vertex = self.pick_vertex(
                        obj,
                        ray
                    )

                    self.selected_vertex = vertex

                    print("Selected Vertex:", vertex)

                    if vertex is not None:

                        self.dragging_object = False
                        self.edge_dragging = False

                        self.vertex_dragging = True

                        self.last_mouse_x = event.x()
                        self.last_mouse_y = event.y()

                        self.vertex_original = np.array(
                            obj.mesh.vertices[vertex],
                            dtype=np.float32
                        )

                    else:

                        self.vertex_dragging = False

                        # -----------------------------
                        # TEMPORARY EDGE TEST
                        # -----------------------------

                        edge = self.pick_edge(
                            obj,
                            ray
                        )

                        self.selected_edge = edge

                        print("Edge Result:", edge)

                        if edge is not None:

                            self.dragging_object = False
                            self.vertex_dragging = False

                            self.edge_dragging = True

                            edge_vertices = obj.mesh.edges[edge]

                            self.edge_vertex_a = edge_vertices[0]
                            self.edge_vertex_b = edge_vertices[1]

                            self.last_mouse_x = event.x()
                            self.last_mouse_y = event.y()

                        else:

                            self.edge_dragging = False

                    self.update()

                    return

            # -------------------------------------------------
            # OBJECT MODE
            # -------------------------------------------------

            obj = self.pick_object()

            print("Picked Object:", obj)

            # ---------------- MOVE ----------------

            if tool == ToolManager.MOVE:

                axis = self.move_gizmo.pick_axis(ray)

                if axis is not None:

                    print("Move Axis:", axis)

                    self.move_gizmo.selected_axis = axis

                    self.history_manager.save_state(
                        self.selected_object
                    )

                    self.last_mouse_x = event.x()
                    self.last_mouse_y = event.y()

                    self.update()

                    return

            # ---------------- ROTATE ----------------

            elif tool == ToolManager.ROTATE:

                rotate_axis = self.rotate_gizmo.pick_axis(ray)

                if rotate_axis is not None:

                    print("Rotate Axis:", rotate_axis)

                    self.rotate_gizmo.selected_axis = rotate_axis

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

                scale_axis = self.scale_gizmo.pick_axis(ray)

                if scale_axis is not None:

                    print("Scale Axis:", scale_axis)

                    self.scale_gizmo.selected_axis = scale_axis

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

                self.set_selected_object(obj)

                self.dragging_object = True

                if abs(ray.direction[1]) > 1e-6:

                    t = (
                        self.drag_plane_y - ray.origin[1]
                    ) / ray.direction[1]

                    hit = ray.origin + ray.direction * t

                    self.drag_offset = (
                        np.array(self.selected_object.position)
                        - hit
                    )

                self.drag_start_x = event.x()
                self.drag_start_y = event.y()

                print("Selected:", obj.name)

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

        print("Viewport Focus:", self.hasFocus())
        
    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:

            # Vertex Drag
            self.vertex_dragging = False

            # Edge Drag
            self.edge_dragging = False
            self.edge_vertex_a = None
            self.edge_vertex_b = None

            # Object Drag
            self.dragging_object = False
            
            # Move Gizmo
            self.move_gizmo.selected_axis = None

            # Rotate Gizmo
            self.rotate_gizmo.selected_axis = None
            self.rotate_gizmo.dragging = False
            self.rotate_gizmo.end_rotation()

            # Scale Gizmo
            self.scale_gizmo.end_scale()

            self._move_saved = False

        elif event.button() == Qt.RightButton:

            self.right_mouse = False

        self.update()

    def mouseMoveEvent(self, event):

        # ---------------------------------
        # Vertex Drag (EDIT MODE)
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

            if self.selected_vertex >= len(mesh.vertices):
                return

            dx = event.x() - self.last_mouse_x
            dy = event.y() - self.last_mouse_y

            sensitivity = 0.01

            x, y, z = mesh.vertices[self.selected_vertex]

            x += dx * sensitivity
            y -= dy * sensitivity

            mesh.vertices[self.selected_vertex] = [x, y, z]

            self.selected_object.bounding_box.update(
                self.selected_object.position,
                self.selected_object.scale
            )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # Edge Drag (EDIT MODE)
        # ---------------------------------

        if (
            self.edge_dragging
            and self.selected_edge is not None
            and self.selected_object is not None
            and self.main_window.mode_manager.get_mode() == "EDIT"
        ):

            mesh = self.selected_object.mesh

            if mesh is None:
                return

            if self.edge_vertex_a is None:
                return

            if self.edge_vertex_b is None:
                return

            if self.edge_vertex_a >= len(mesh.vertices):
                return

            if self.edge_vertex_b >= len(mesh.vertices):
                return

            dx = event.x() - self.last_mouse_x
            dy = event.y() - self.last_mouse_y

            sensitivity = 0.01

            print("\n=========================")
            print("Dragging Object :", self.selected_object.name)
            print("Mesh ID         :", id(mesh))
            print("Edge            :", self.selected_edge)

            va = mesh.vertices[self.edge_vertex_a]
            vb = mesh.vertices[self.edge_vertex_b]

            print("Before A :", va)
            print("Before B :", vb)

            va[0] += dx * sensitivity
            va[1] -= dy * sensitivity

            vb[0] += dx * sensitivity
            vb[1] -= dy * sensitivity

            mesh.vertices[self.edge_vertex_a] = va
            mesh.vertices[self.edge_vertex_b] = vb

            print("After A :", mesh.vertices[self.edge_vertex_a])
            print("After B :", mesh.vertices[self.edge_vertex_b])

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # Scale Gizmo
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
        # Rotate Gizmo
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

            self.rotate_gizmo.rotate(ray)

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # ---------------------------------
        # Move Gizmo
        # ---------------------------------

        if (
            event.buttons() & Qt.LeftButton
            and self.move_gizmo.selected_axis is not None
            and self.selected_object is not None
        ):

            if not hasattr(self, "_move_saved"):

                self.history_manager.save_state(
                    self.selected_object
                )

                self._move_saved = True

            dx = event.x() - self.last_mouse_x
            dy = event.y() - self.last_mouse_y

            speed = 0.003

            if self.move_gizmo.selected_axis == "X":

                self.selected_object.translate(
                    dx * speed,
                    0.0,
                    0.0
                )

            elif self.move_gizmo.selected_axis == "Y":

                self.selected_object.translate(
                    0.0,
                    -dy * speed,
                    0.0
                )

            elif self.move_gizmo.selected_axis == "Z":

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
        # Object Drag
        # ---------------------------------

        if self.dragging_object and self.selected_object:

            ray = RayBuilder.build_ray(
                event.x(),
                event.y(),
                self,
                self.camera
            )

            t = (
                self.drag_plane_y - ray.origin[1]
            ) / ray.direction[1]

            hit = ray.origin + ray.direction * t

            new_position = hit + self.drag_offset

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
        # Camera Rotation
        # ---------------------------------

        if event.buttons() & Qt.RightButton:

            dx = event.x() - self.last_mouse_x
            dy = event.y() - self.last_mouse_y

            self.camera.yaw -= dx * 0.5
            self.camera.pitch += dy * 0.5

            self.camera.pitch = max(
                -89,
                min(89, self.camera.pitch)
            )

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()
        
    def keyPressEvent(self, event):

        print("VIEWPORT KEY:", event.key())

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
        # MOVE
        # ---------------------------------
        if event.key() == Qt.Key_W:

            print("MOVE")

            self.tool_manager.set_tool(ToolManager.MOVE)

            self.update()

            return

        # ---------------------------------
        # ROTATE
        # ---------------------------------
        elif event.key() == Qt.Key_E:

            print("ROTATE")

            self.tool_manager.set_tool(ToolManager.ROTATE)

            self.update()

            return

        # ---------------------------------
        # SCALE
        # ---------------------------------
        elif event.key() == Qt.Key_R:

            print("SCALE")

            self.tool_manager.set_tool(ToolManager.SCALE)

            self.update()

            return

        elif event.key() == Qt.Key_F4:

            self.main_window.mode_manager.toggle()

            print(self.main_window.mode_manager.get_mode())

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

