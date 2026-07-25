from OpenGL.GL import *
import numpy as np

from scene.bounding_box import BoundingBox
from scene.raycast import RayCaster


class ScaleGizmo:

    def __init__(self):

        self.target = None

        self.selected_axis = None

        self.dragging = False

        self.axis_length = 2.0

        self.handle_size = 0.12

        self.uniform_size = 0.15

        self.start_mouse_x = 0
        self.start_mouse_y = 0

        self.start_scale = [1.0, 1.0, 1.0]

        self.raycaster = RayCaster()

        self.x_box = BoundingBox(
            [0, 0, 0],
            [0.20, 0.20, 0.20]
        )

        self.y_box = BoundingBox(
            [0, 0, 0],
            [0.20, 0.20, 0.20]
        )

        self.z_box = BoundingBox(
            [0, 0, 0],
            [0.20, 0.20, 0.20]
        )

        self.center_box = BoundingBox(
            [0, 0, 0],
            [0.25, 0.25, 0.25]
        )

    def set_target(self, obj):

        self.target = obj

        if obj is None:
            return

        self.update_boxes()

    def update_boxes(self):

        if self.target is None:
            return

        p = self.target.position

        self.x_box.update(
            [
                p[0] + self.axis_length,
                p[1],
                p[2]
            ]
        )

        self.y_box.update(
            [
                p[0],
                p[1] + self.axis_length,
                p[2]
            ]
        )

        self.z_box.update(
            [
                p[0],
                p[1],
                p[2] + self.axis_length
            ]
        )

        self.center_box.update(
            [
                p[0],
                p[1],
                p[2]
            ]
        )

    def begin_scale(self, axis, ray):

        self.selected_axis = axis

        self.dragging = True

        self.start_scale = self.target.scale.copy()

    def end_scale(self):

        self.dragging = False

        self.selected_axis = None

    def pick_axis(self, ray):

        if self.target is None:
            return None

        self.update_boxes()

        if self.raycaster.intersect_aabb(
            ray,
            self.center_box.minimum,
            self.center_box.maximum
        ) is not None:

            return "XYZ"

        if self.raycaster.intersect_aabb(
            ray,
            self.x_box.minimum,
            self.x_box.maximum
        ) is not None:

            return "X"

        if self.raycaster.intersect_aabb(
            ray,
            self.y_box.minimum,
            self.y_box.maximum
        ) is not None:

            return "Y"

        if self.raycaster.intersect_aabb(
            ray,
            self.z_box.minimum,
            self.z_box.maximum
        ) is not None:

            return "Z"

        return None

    def scale(
        self,
        mouse_x,
        mouse_y,
        last_mouse_x,
        last_mouse_y
    ):

        if self.target is None:
            return

        dx = mouse_x - last_mouse_x
        dy = mouse_y - last_mouse_y

        delta = (dx - dy) * 0.01

        if self.selected_axis == "X":

            self.target.scale[0] += delta

        elif self.selected_axis == "Y":

            self.target.scale[1] += delta

        elif self.selected_axis == "Z":

            self.target.scale[2] += delta

        elif self.selected_axis == "XYZ":

            self.target.scale[0] += delta
            self.target.scale[1] += delta
            self.target.scale[2] += delta

        self.target.scale[0] = max(
            0.1,
            self.target.scale[0]
        )

        self.target.scale[1] = max(
            0.1,
            self.target.scale[1]
        )

        self.target.scale[2] = max(
            0.1,
            self.target.scale[2]
        )

    def draw(self, camera):

        print("DRAW SCALE GIZMO")

        if self.target is None:
            return

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()

        x = self.target.position[0]
        y = self.target.position[1]
        z = self.target.position[2]

        glTranslatef(x, y, z)

        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

        glLineWidth(4)

        # -----------------------------
        # X Axis
        # -----------------------------
        glColor3f(1, 0, 0)

        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(self.axis_length, 0, 0)
        glEnd()

        # X Handle
        glPointSize(10)

        glBegin(GL_POINTS)
        glVertex3f(self.axis_length, 0, 0)
        glEnd()
        # -----------------------------
        # Y Axis
        # -----------------------------
        glColor3f(0, 1, 0)

        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, self.axis_length, 0)
        glEnd()

        # Y Handle
        glPointSize(10)

        glBegin(GL_POINTS)
        glVertex3f(0, self.axis_length, 0)
        glEnd()

        # -----------------------------
        # Z Axis
        # -----------------------------
        glColor3f(0, 0, 1)

        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, self.axis_length)
        glEnd()

        # Z Handle
        glPointSize(10)

        glBegin(GL_POINTS)
        glVertex3f(0, 0, self.axis_length)
        glEnd()
        # -----------------------------
        # Uniform Scale Handle (Center)
        # -----------------------------
        glColor3f(1.0, 1.0, 0.0)
        self.draw_uniform_handle()

        glLineWidth(1)

        glPopMatrix()
        glPopAttrib()

    def draw_uniform_handle(self):

        s = self.uniform_size

        glBegin(GL_QUADS)

        # Front
        glVertex3f(-s,-s,s)
        glVertex3f(s,-s,s)
        glVertex3f(s,s,s)
        glVertex3f(-s,s,s)

        # Back
        glVertex3f(s,-s,-s)
        glVertex3f(-s,-s,-s)
        glVertex3f(-s,s,-s)
        glVertex3f(s,s,-s)

        # Left
        glVertex3f(-s,-s,-s)
        glVertex3f(-s,-s,s)
        glVertex3f(-s,s,s)
        glVertex3f(-s,s,-s)

        # Right
        glVertex3f(s,-s,s)
        glVertex3f(s,-s,-s)
        glVertex3f(s,s,-s)
        glVertex3f(s,s,s)

        # Top
        glVertex3f(-s,s,s)
        glVertex3f(s,s,s)
        glVertex3f(s,s,-s)
        glVertex3f(-s,s,-s)

        # Bottom
        glVertex3f(-s,-s,-s)
        glVertex3f(s,-s,-s)
        glVertex3f(s,-s,s)
        glVertex3f(-s,-s,s)

        glEnd()

    def draw_handle(
        self,
        x,
        y,
        z
    ):

        glPushMatrix()

        glTranslatef(x, y, z)

        s = self.handle_size

        glBegin(GL_QUADS)

        # Front
        glVertex3f(-s,-s,s)
        glVertex3f(s,-s,s)
        glVertex3f(s,s,s)
        glVertex3f(-s,s,s)

        # Back
        glVertex3f(s,-s,-s)
        glVertex3f(-s,-s,-s)
        glVertex3f(-s,s,-s)
        glVertex3f(s,s,-s)

        # Left
        glVertex3f(-s,-s,-s)
        glVertex3f(-s,-s,s)
        glVertex3f(-s,s,s)
        glVertex3f(-s,s,-s)

        # Right
        glVertex3f(s,-s,s)
        glVertex3f(s,-s,-s)
        glVertex3f(s,s,-s)
        glVertex3f(s,s,s)

        # Top
        glVertex3f(-s,s,s)
        glVertex3f(s,s,s)
        glVertex3f(s,s,-s)
        glVertex3f(-s,s,-s)

        # Bottom
        glVertex3f(-s,-s,-s)
        glVertex3f(s,-s,-s)
        glVertex3f(s,-s,s)
        glVertex3f(-s,-s,s)

        glEnd()

        glPopMatrix()