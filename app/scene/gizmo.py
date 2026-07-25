from OpenGL.GL import *
from app.scene.bounding_box import BoundingBox
from scene.gizmo_axis import GizmoAxis
from scene.raycast import RayCaster

class MoveGizmo:

    def __init__(self):

        self.target = None

        self.selected_axis = None

        self.axis_length = 2.0

        self.x_axis = GizmoAxis("X")
        self.y_axis = GizmoAxis("Y")
        self.z_axis = GizmoAxis("Z")

        self.xy_plane = BoundingBox([0, 0, 0], [0.45, 0.45, 0.02])
        self.yz_plane = BoundingBox([0, 0, 0], [0.02, 0.45, 0.45])
        self.xz_plane = BoundingBox([0, 0, 0], [0.45, 0.02, 0.45])

    def set_target(self, obj):

        self.target = obj

        if obj is None:
            return

        self.x_axis.update(obj.position)
        self.y_axis.update(obj.position)
        self.z_axis.update(obj.position)

        self.xy_plane.update(
            [
                obj.position[0] + 0.25,
                obj.position[1] + 0.25,
                obj.position[2]
            ]
        )

        self.yz_plane.update(
            [
                obj.position[0],
                obj.position[1] + 0.25,
                obj.position[2] + 0.25
            ]
        )

        self.xz_plane.update(
            [
                obj.position[0] + 0.25,
                obj.position[1],
                obj.position[2] + 0.25
            ]
        )

        p = obj.position
        s = self.axis_length

        self.xy_plane.update(
            [
                obj.position[0] + 0.6,
                obj.position[1] + 0.6,
                obj.position[2]
            ],
            [
                0.6,
                0.6,
                0.01
            ]
        )

        self.yz_plane.update(
            [
                obj.position[0],
                obj.position[1] + 0.6,
                obj.position[2] + 0.6
            ],
            [
                0.01,
                0.6,
                0.6
            ]
        )

        self.xz_plane.update(
            [
                obj.position[0] + 0.6,
                obj.position[1],
                obj.position[2] + 0.6
            ],
            [
                0.6,
                0.01,
                0.6
            ]
        )

    def draw(self, camera):

        if self.target is None:
            return

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()

        glTranslatef(
            self.target.position[0],
            self.target.position[1],
            self.target.position[2]
        )

        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

        glLineWidth(6)

        glBegin(GL_LINES)

        # X Axis
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(self.axis_length, 0.0, 0.0)

        # Y Axis
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, self.axis_length, 0.0)

        # Z Axis
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, self.axis_length)

        glEnd()

        glLineWidth(1)

        glPopMatrix()
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glColor4f(1, 1, 1, 1)
        glPopAttrib()

    def pick_axis(self, ray):

        if self.target is None:
            return None

        raycaster = RayCaster()

        self.selected_axis = None

        if raycaster.intersect_aabb(
            ray,
            self.x_axis.bounding_box.minimum,
            self.x_axis.bounding_box.maximum
        ) is not None:

            self.selected_axis = "X"
            return "X"

        if raycaster.intersect_aabb(
            ray,
            self.y_axis.bounding_box.minimum,
            self.y_axis.bounding_box.maximum
        ) is not None:

            self.selected_axis = "Y"
            return "Y"

        if raycaster.intersect_aabb(
            ray,
            self.z_axis.bounding_box.minimum,
            self.z_axis.bounding_box.maximum
        ) is not None:

            self.selected_axis = "Z"
            return "Z"

        return None