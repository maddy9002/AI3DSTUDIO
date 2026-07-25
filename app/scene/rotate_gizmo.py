import math
import numpy as np
from OpenGL.GL import *

class RotateGizmo:

    def __init__(self):

        self.target = None

        self.selected_axis = None

        self.radius = 1.2

        self.dragging = False

        self.start_angle = 0.0

        self.current_angle = 0.0

        self.rotation_plane_normal = None

    def set_target(self, obj):

        self.target = obj

    def draw(self):

        if self.target is None:
            return

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()

        try:

            glDisable(GL_LIGHTING)
            glDisable(GL_TEXTURE_2D)
            glDisable(GL_BLEND)

            glEnable(GL_DEPTH_TEST)

            glLineWidth(4)

            x = self.target.position[0]
            y = self.target.position[1]
            z = self.target.position[2]

            glTranslatef(x, y, z)

            # X Ring
            if self.selected_axis == "X":
                glColor3f(1.0, 1.0, 0.0)
            else:
                glColor3f(1.0, 0.0, 0.0)

            self.draw_x_ring()

            # Y Ring
            if self.selected_axis == "Y":
                glColor3f(1.0, 1.0, 0.0)
            else:
                glColor3f(0.0, 1.0, 0.0)

            self.draw_y_ring()

            # Z Ring
            if self.selected_axis == "Z":
                glColor3f(1.0, 1.0, 0.0)
            else:
                glColor3f(0.0, 0.6, 1.0)

            self.draw_z_ring()

        finally:

            glLineWidth(1)

            glPopMatrix()

            glEnable(GL_LIGHTING)
            glDisable(GL_BLEND)
            glDepthMask(GL_TRUE)
            glColor4f(1, 1, 1, 1)

            glPopAttrib()
            
    def draw_x_ring(self):

        glBegin(GL_LINE_LOOP)

        for i in range(128):

            angle = (2.0 * math.pi * i) / 128

            glVertex3f(
                0.0,
                self.radius * math.cos(angle),
                self.radius * math.sin(angle)
            )

        glEnd()

    def draw_y_ring(self):

        glBegin(GL_LINE_LOOP)

        for i in range(128):

            angle = (2.0 * math.pi * i) / 128

            glVertex3f(
                self.radius * math.cos(angle),
                0.0,
                self.radius * math.sin(angle)
            )

        glEnd()

    def draw_z_ring(self):

        glBegin(GL_LINE_LOOP)

        for i in range(128):

            angle = (2.0 * math.pi * i) / 128

            glVertex3f(
                self.radius * math.cos(angle),
                self.radius * math.sin(angle),
                0.0
            )

        glEnd()

    def begin_rotation(self, axis, ray):

        self.selected_axis = axis

        self.dragging = True

        if axis == "X":

            plane = [1,0,0]

        elif axis == "Y":

            plane = [0,1,0]

        else:

            plane = [0,0,1]

        hit = self.ray_plane_intersection(
            ray,
            plane
        )

        if hit is None:

            self.start_angle = 0

        else:

            self.start_angle = self.calculate_angle(hit)

    def end_rotation(self):

        self.dragging = False

        self.selected_axis = None

    def rotate(self, ray):

        if self.target is None:
            return

        print("--------------------------------")
        print("Rotate() CALLED")
        print("Selected Axis:", self.selected_axis)

        if self.selected_axis == "X":

            plane = [1,0,0]

        elif self.selected_axis == "Y":

            plane = [0,1,0]

        else:

            plane = [0,0,1]

        hit = self.ray_plane_intersection(
            ray,
            plane
        )

        print("HIT:", hit)

        if hit is None:
            return

        angle = self.calculate_angle(hit)

        delta = self.start_angle - angle

        print("Start Angle:", self.start_angle)
        print("Current Angle:", angle)
        print("Delta:", delta)
        print("Rotation Before:", self.target.rotation)

        if self.selected_axis == "X":

            self.target.rotation[0] += delta

        elif self.selected_axis == "Y":

            self.target.rotation[1] += delta

        else:

            self.target.rotation[2] -= delta

        print("Rotation After:", self.target.rotation)

        self.start_angle = angle
        
    def pick_axis(self, ray):

        if self.target is None:
            return None

        center = np.array(self.target.position, dtype=float)

        tolerance = 0.15

        planes = {
            "X": np.array([1.0, 0.0, 0.0]),
            "Y": np.array([0.0, 1.0, 0.0]),
            "Z": np.array([0.0, 0.0, 1.0])
        }

        for axis, normal in planes.items():

            denom = np.dot(ray.direction, normal)

            if abs(denom) < 1e-6:
                continue

            t = np.dot(center - ray.origin, normal) / denom

            if t < 0:
                continue

            hit = ray.origin + ray.direction * t

            distance = np.linalg.norm(hit - center)

            if abs(distance - self.radius) < tolerance:

                self.selected_axis = axis

                return axis

        return None
    
    def ray_plane_intersection(self, ray, plane_normal):

        if self.target is None:
            return None

        center = np.array(self.target.position, dtype=float)

        plane_normal = np.array(plane_normal, dtype=float)

        denom = np.dot(ray.direction, plane_normal)

        if abs(denom) < 0.00001:
            return None

        t = np.dot(center - ray.origin, plane_normal) / denom

        if t < 0:
            return None

        return ray.origin + ray.direction * t
    
    def calculate_angle(self, point):

        center = np.array(self.target.position, dtype=float)

        p = point - center

        if self.selected_axis == "X":

            return np.degrees(np.arctan2(
                p[1],
                p[2]
            ))

        elif self.selected_axis == "Y":

            return np.degrees(np.arctan2(
                p[2],
                p[0]
            ))

        else:

            return np.degrees(np.arctan2(
                p[1],
                p[0]
            ))