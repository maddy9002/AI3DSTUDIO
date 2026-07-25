class ToolManager:

    SELECT = "select"
    MOVE = "move"
    ROTATE = "rotate"
    SCALE = "scale"

    def __init__(self):
        self.current_tool = self.SELECT

    def set_tool(self, tool):
        self.current_tool = tool

    def get_tool(self):
        return self.current_tool