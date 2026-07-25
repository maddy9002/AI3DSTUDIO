class CommandExecutor:

    def __init__(self, studio):

        self.studio = studio

    def execute(self, command, argument):

        print("EXECUTING:", command)

        if command == "create_cube":

            print("Calling create_cube()")

            self.studio.create_cube()

            return

        if command == "delete_selected":

            self.studio.delete_selected_object()

            return

        if command == "duplicate_selected":

            self.studio.duplicate_selected_object()

            return

        print("UNKNOWN COMMAND")

        self.studio.ai_console.append(
            f"Unknown command: {argument}"
        )