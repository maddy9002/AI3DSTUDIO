from OpenGL.GL import *
from OpenGL.GLU import *
import math

class MeshRenderer:

    @staticmethod
    def draw(mesh):

        if mesh is None:
            return

        glBegin(GL_QUADS)

        for face in mesh.faces:

            for vertex_index in face:

                x, y, z = mesh.vertices[vertex_index]

                glVertex3f(x, y, z)

        glEnd()

    @staticmethod
    def draw_sphere():

        quad = gluNewQuadric()

        gluSphere(
            quad,
            0.5,
            32,
            32
        )

        gluDeleteQuadric(quad)

    @staticmethod
    def draw_cylinder():

        quad = gluNewQuadric()

        glPushMatrix()

        glTranslatef(0,0,-0.5)

        # Side
        gluCylinder(
            quad,
            0.5,
            0.5,
            1.0,
            32,
            8
        )

        # Bottom
        glPushMatrix()

        glRotatef(180,1,0,0)

        gluDisk(
            quad,
            0.0,
            0.5,
            32,
            1
        )

        glPopMatrix()

        # Top
        glPushMatrix()

        glTranslatef(0,0,1.0)

        gluDisk(
            quad,
            0.0,
            0.5,
            32,
            1
        )

        glPopMatrix()

        glPopMatrix()

        gluDeleteQuadric(quad)
        
    @staticmethod
    def draw_cone():

        quad = gluNewQuadric()

        glPushMatrix()

        glTranslatef(0,0,-0.5)

        gluCylinder(
            quad,
            0.5,
            0.0,
            1.0,
            32,
            8
        )

        glPopMatrix()

        gluDeleteQuadric(quad)

    @staticmethod
    def draw_plane():

        glBegin(GL_QUADS)

        glVertex3f(-0.5,0,-0.5)
        glVertex3f(0.5,0,-0.5)
        glVertex3f(0.5,0,0.5)
        glVertex3f(-0.5,0,0.5)

        glEnd()

    @staticmethod
    def draw_torus():

        major_radius = 0.6
        minor_radius = 0.2

        major_segments = 48
        minor_segments = 24

        for i in range(major_segments):

            theta1 = (2 * math.pi * i) / major_segments
            theta2 = (2 * math.pi * (i + 1)) / major_segments

            glBegin(GL_QUAD_STRIP)

            for j in range(minor_segments + 1):

                phi = (2 * math.pi * j) / minor_segments

                cos_phi = math.cos(phi)
                sin_phi = math.sin(phi)

                # -------- First Ring --------

                cos_theta = math.cos(theta1)
                sin_theta = math.sin(theta1)

                x = (major_radius + minor_radius * cos_phi) * cos_theta
                y = (major_radius + minor_radius * cos_phi) * sin_theta
                z = minor_radius * sin_phi

                glVertex3f(x, y, z)

                # -------- Second Ring --------

                cos_theta = math.cos(theta2)
                sin_theta = math.sin(theta2)

                x = (major_radius + minor_radius * cos_phi) * cos_theta
                y = (major_radius + minor_radius * cos_phi) * sin_theta
                z = minor_radius * sin_phi

                glVertex3f(x, y, z)

            glEnd()

