class ToolManager:

    MOVE = 0
    ROTATE = 1
    SCALE = 2

    def __init__(self):

        self.current_tool = ToolManager.MOVE

    def set_tool(self, tool):

        print("BEFORE:", self.current_tool)

        self.current_tool = tool

        print("AFTER :", self.current_tool)

    def get_tool(self):

        print("GET TOOL:", self.current_tool)

        return self.current_tool