class CommandParser:

    def parse(self, text):

        command = text.lower().strip()

        # -------------------------
        # Create Commands
        # -------------------------

        cube_commands = [

            "create cube",
            "add cube",
            "make cube",
            "spawn cube",
            "cube",
            "new cube",
            "create another cube",
            "make another cube",
            "create a cube",
            "make a cube"

        ]

        sphere_commands = [

            "create sphere",
            "add sphere",
            "make sphere",
            "spawn sphere",
            "sphere",
            "new sphere"

        ]

        plane_commands = [

            "create plane",
            "add plane",
            "make plane",
            "spawn plane",
            "plane",
            "new plane"

        ]

        cylinder_commands = [

            "create cylinder",
            "add cylinder",
            "make cylinder",
            "spawn cylinder",
            "cylinder",
            "new cylinder"

        ]

        cone_commands = [

            "create cone",
            "add cone",
            "make cone",
            "spawn cone",
            "cone",
            "new cone"

        ]

        torus_commands = [

            "create torus",
            "add torus",
            "make torus",
            "spawn torus",
            "torus",
            "new torus"

        ]

        # -------------------------
        # Edit Commands
        # -------------------------

        delete_commands = [

            "delete",
            "delete selected",
            "remove selected",
            "remove cube",
            "delete cube"

        ]

        duplicate_commands = [

            "duplicate",
            "duplicate selected",
            "copy",
            "copy selected",
            "clone"

        ]

        # -------------------------
        # Return Commands
        # -------------------------

        if command in cube_commands:
            return ("create_cube", None)

        if command in sphere_commands:
            return ("create_sphere", None)

        if command in plane_commands:
            return ("create_plane", None)

        if command in cylinder_commands:
            return ("create_cylinder", None)

        if command in cone_commands:
            return ("create_cone", None)

        if command in torus_commands:
            return ("create_torus", None)

        if command in delete_commands:
            return ("delete_selected", None)

        if command in duplicate_commands:
            return ("duplicate_selected", None)

        return ("unknown", command)