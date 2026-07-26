class CommandExecutor:

    def __init__(self, studio):

        self.studio = studio

    def execute(self, command, argument):

        print("EXECUTING:", command)

        # -------------------------
        # Create Commands
        # -------------------------

        if command == "create_cube":
            print("Calling create_cube()")
            self.studio.create_cube()
            return

        if command == "create_sphere":
            print("Calling create_sphere()")
            self.studio.create_sphere()
            return

        if command == "create_plane":
            print("Calling create_plane()")
            self.studio.create_plane()
            return

        if command == "create_cylinder":
            print("Calling create_cylinder()")
            self.studio.create_cylinder()
            return

        if command == "create_cone":
            print("Calling create_cone()")
            self.studio.create_cone()
            return

        if command == "create_torus":
            print("Calling create_torus()")
            self.studio.create_torus()
            return

        # -------------------------
        # Edit Commands
        # -------------------------

        if command == "delete_selected":
            self.studio.delete_selected_object()
            return

        if command == "duplicate_selected":
            self.studio.duplicate_selected_object()
            return

        # -------------------------
        # Unknown Command
        # -------------------------

        print("UNKNOWN COMMAND")

        self.studio.ai_console.append(
            f"Unknown command: {argument}"
        )