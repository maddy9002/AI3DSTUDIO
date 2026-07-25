class SelectionManager:

    def __init__(self, viewport):

        self.viewport = viewport

        self.selected_object = None

    def select(self, obj):

        self.selected_object = obj

        self.viewport.move_gizmo.set_target(obj)
        self.viewport.rotate_gizmo.set_target(obj)
        self.viewport.scale_gizmo.set_target(obj)

        self.viewport.update()

    def deselect(self):

        self.selected_object = None

        self.viewport.move_gizmo.set_target(None)
        self.viewport.rotate_gizmo.set_target(None)
        self.viewport.scale_gizmo.set_target(None)

        self.viewport.update()

    def get_selected(self):

        return self.selected_object

    def has_selection(self):

        return self.selected_object is not None