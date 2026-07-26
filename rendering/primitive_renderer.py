from OpenGL.GL import *
from OpenGL.GLU import * 
from OpenGL.GLUT import *


class PrimitiveRenderer:

    @staticmethod
    def draw_cube():

        glutSolidCube(1.0)

    @staticmethod
    def draw_sphere():

        glutSolidSphere(
            0.5,
            32,
            32
        )

    @staticmethod
    def draw_plane():

        glBegin(GL_QUADS)

        glNormal3f(0, 1, 0)

        glVertex3f(-0.5, 0.0, -0.5)
        glVertex3f(0.5, 0.0, -0.5)
        glVertex3f(0.5, 0.0, 0.5)
        glVertex3f(-0.5, 0.0, 0.5)

        glEnd()

    @staticmethod
    def draw_cylinder():

        quad = gluNewQuadric()

        gluCylinder(
            quad,
            0.5,
            0.5,
            1.0,
            32,
            8
        )

        gluDeleteQuadric(quad)

    @staticmethod
    def draw_cone():

        glutSolidCone(
            0.5,
            1.0,
            32,
            16
        )

    @staticmethod
    def draw_torus():

        glutSolidTorus(
            0.15,
            0.4,
            24,
            48
        )