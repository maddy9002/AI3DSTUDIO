class GestureController:

    def __init__(self):

        self.selected_object = None

        self.is_grabbing = False

        self.cursor_x = 0.0
        self.cursor_y = 0.0

        # Hand orientation when grabbing
        self.grab_axes = None

        # Object rotation when grabbing
        self.grab_rotation = None

        # Object scale when grabbing
        self.grab_scale = None

    def update_cursor(self, x, y):

        self.cursor_x = x
        self.cursor_y = y

    def grab(self, obj, axes):

        if self.is_grabbing:
            return

        self.selected_object = obj

        self.is_grabbing = True

        self.grab_axes = axes

        self.grab_rotation = obj.rotation.copy()

        self.grab_scale = obj.scale.copy()

    def release(self):

        self.is_grabbing = False

        self.selected_object = None

        self.grab_axes = None

        self.grab_rotation = None

        self.grab_scale = None