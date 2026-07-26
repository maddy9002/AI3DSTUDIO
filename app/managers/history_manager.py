import copy


class HistoryManager:

    def __init__(self):

        self.undo_stack = []
        self.redo_stack = []

    def save_state(self, scene_object):

        state = {
            "object": scene_object,
            "position": copy.deepcopy(scene_object.position),
            "rotation": copy.deepcopy(scene_object.rotation),
            "scale": copy.deepcopy(scene_object.scale)
        }

        self.undo_stack.append(state)

        # Once a new action happens, redo history is no longer valid
        self.redo_stack.clear()

    def undo(self):

        if not self.undo_stack:
            return

        state = self.undo_stack.pop()

        obj = state["object"]

        redo_state = {
            "object": obj,
            "position": copy.deepcopy(obj.position),
            "rotation": copy.deepcopy(obj.rotation),
            "scale": copy.deepcopy(obj.scale)
        }

        self.redo_stack.append(redo_state)

        obj.position = copy.deepcopy(state["position"])
        obj.rotation = copy.deepcopy(state["rotation"])
        obj.scale = copy.deepcopy(state["scale"])

    def redo(self):

        if not self.redo_stack:
            return

        state = self.redo_stack.pop()

        obj = state["object"]

        undo_state = {
            "object": obj,
            "position": copy.deepcopy(obj.position),
            "rotation": copy.deepcopy(obj.rotation),
            "scale": copy.deepcopy(obj.scale)
        }

        self.undo_stack.append(undo_state)

        obj.position = copy.deepcopy(state["position"])
        obj.rotation = copy.deepcopy(state["rotation"])
        obj.scale = copy.deepcopy(state["scale"])