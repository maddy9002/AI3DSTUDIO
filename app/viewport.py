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

class Viewport(QOpenGLWidget):

    def __init__(self):
        super().__init__()

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

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

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

            obj.bounding_box.update(
                obj.position,
                obj.scale
            )

            glPushMatrix()

            world_position = obj.get_world_position()
            world_rotation = obj.get_world_rotation()
            world_scale = obj.get_world_scale()

            glTranslatef(
                world_position[0],
                world_position[1],
                world_position[2]
            )

            glRotatef(world_rotation[0],1,0,0)
            glRotatef(world_rotation[1],0,1,0)
            glRotatef(world_rotation[2],0,0,1)

            glScalef(
                world_scale[0],
                world_scale[1],
                world_scale[2]
            )

            if obj == self.selected_object:
                glColor3f(1.0, 1.0, 0.0)
            else:
                glColor3f(0.0, 1.0, 0.0)

            if obj.object_type == "Cube":

                if obj.mesh is not None:

                    MeshRenderer.draw(obj.mesh)

                else:

                    self.draw_cube()

            elif obj.object_type == "Sphere":

                MeshRenderer.draw_sphere()

            elif obj.object_type == "Plane":

                MeshRenderer.draw_plane()

            elif obj.object_type == "Cylinder":

                MeshRenderer.draw_cylinder()

            elif obj.object_type == "Cone":

                MeshRenderer.draw_cone()

            elif obj.object_type == "Torus":

                MeshRenderer.draw_torus()

            else:

                self.draw_cube()

            glPopMatrix()

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

            obj = self.pick_object()
            print("Picked Object:", obj)

            ray = RayBuilder.build_ray(
                self.mouse_x,
                self.mouse_y,
                self,
                self.camera
            )

            tool = self.tool_manager.get_tool()

            # ---------------------------------
            # MOVE TOOL
            # ---------------------------------
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

            # ---------------------------------
            # ROTATE TOOL
            # ---------------------------------
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

            # ---------------------------------
            # SCALE TOOL
            # ---------------------------------
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

            # ---------------------------------
            # OBJECT SELECTION
            # ---------------------------------

            if obj is not None:

                self.set_selected_object(obj)

                self.dragging_object = True

                ray = RayBuilder.build_ray(
                    self.mouse_x,
                    self.mouse_y,
                    self,
                    self.camera
                )

                if abs(ray.direction[1]) > 1e-6:

                    t = (self.drag_plane_y - ray.origin[1]) / ray.direction[1]

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

        # ---------------------------------
        # RIGHT MOUSE
        # ---------------------------------

        if event.button() == Qt.RightButton:

            self.right_mouse = True

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()
            
    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:

            # Stop object dragging
            self.dragging_object = False

            # Stop move gizmo
            self.move_gizmo.selected_axis = None

            # Stop rotate gizmo
            self.rotate_gizmo.selected_axis = None
            self.rotate_gizmo.dragging = False
            self.rotate_gizmo.end_rotation()

            self.scale_gizmo.end_scale()

            self._move_saved = False

        elif event.button() == Qt.RightButton:

            self.right_mouse = False

        self.update()

    def mouseMoveEvent(self, event):

        # -----------------------------
        # Scale Gizmo Drag
        # -----------------------------

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

        # -----------------------------
        # Rotate Gizmo Drag
        # -----------------------------
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

        # -----------------------------
        # Gizmo Drag
        # -----------------------------
        print("Buttons:", event.buttons())
        print("Selected Axis:", self.move_gizmo.selected_axis)
        print("Selected Object:", self.selected_object)

        if not hasattr(self, "_move_saved"):
            self.history_manager.save_state(self.selected_object)
            self._move_saved = True

        if (
            event.buttons() & Qt.LeftButton
            and self.move_gizmo.selected_axis is not None
            and self.selected_object is not None
        ):
            
            print("Dragging:", self.move_gizmo.selected_axis)

            dx = event.x() - self.last_mouse_x
            dy = event.y() - self.last_mouse_y

            speed = 0.003

            if self.move_gizmo.selected_axis == "X":
                self.selected_object.position[0] += dx * speed

            elif self.move_gizmo.selected_axis == "Y":
                self.selected_object.position[1] -= dy * speed

            elif self.move_gizmo.selected_axis == "Z":
                self.selected_object.position[2] += dx * speed

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return
        
        if self.dragging_object and self.selected_object:

            ray = RayBuilder.build_ray(
                event.x(),
                event.y(),
                self,
                self.camera
            )

            t = (self.drag_plane_y - ray.origin[1]) / ray.direction[1]

            hit = ray.origin + ray.direction * t

            new_position = hit + self.drag_offset

            self.selected_object.position[0] = float(new_position[0])
            self.selected_object.position[2] = float(new_position[2])

            self.last_mouse_x = event.x()
            self.last_mouse_y = event.y()

            self.update()

            return

        # -----------------------------
        # Camera Rotation
        # -----------------------------
        if event.buttons() & Qt.RightButton:

            print("Rotating Camera")

            dx = event.x() - self.last_mouse_x
            dy = event.y() - self.last_mouse_y

            self.camera.yaw -= dx * 0.5
            self.camera.pitch += dy * 0.5

            self.camera.pitch = max(-89, min(89, self.camera.pitch))

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