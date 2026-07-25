import bpy
import math

bpy.ops.object.select_all(
    action='SELECT'
)

bpy.ops.object.delete()

# Fuselage

bpy.ops.mesh.primitive_cylinder_add(
    radius=0.15,
    depth=2.0,
    location=(0, 0, 0)
)

fuselage = bpy.context.active_object

fuselage.rotation_euler[0] = math.radians(
    90
)

# Main Wing

bpy.ops.mesh.primitive_cube_add(
    location=(0, 0, 0)
)

wing = bpy.context.active_object

wing.scale = (
    3,
    0.25,
    0.03
)

# Horizontal Tail

bpy.ops.mesh.primitive_cube_add(
    location=(-0.9, 0, 0)
)

tail = bpy.context.active_object

tail.scale = (
    0.8,
    0.15,
    0.03
)

# Vertical Tail

bpy.ops.mesh.primitive_cube_add(
    location=(-0.9, 0, 0.25)
)

vtail = bpy.context.active_object

vtail.scale = (
    0.08,
    0.15,
    0.35
)

print(
    "Glider Created"
)