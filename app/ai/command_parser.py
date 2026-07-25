class CommandParser:

    def parse(self, text):

        command = text.lower().strip()

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

        if command in cube_commands:
            return ("create_cube", None)

        if command in delete_commands:
            return ("delete_selected", None)

        if command in duplicate_commands:
            return ("duplicate_selected", None)

        return ("unknown", command)