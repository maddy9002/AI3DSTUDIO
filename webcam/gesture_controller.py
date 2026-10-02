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

        # --------------------------------------------------------
        # WAVE GESTURE
        # --------------------------------------------------------

        self.wave_history = []

        self.wave_direction = None

        self.wave_count = 0

        self.wave_active = False

        self.wave_cooldown = 0

        self.wave_min_movement = 0.08

        self.wave_direction_changes_required = 2

        self.wave_history_size = 12

    def update_cursor(self, x, y):

        self.cursor_x = x
        self.cursor_y = y

    # ------------------------------------------------------------
    # WAVE DETECTION
    # ------------------------------------------------------------

    def update_wave(self, x):

        """
        Update the horizontal hand movement used for
        wave detection.

        Returns True once when a complete wave is detected.
        """

        if self.wave_cooldown > 0:

            self.wave_cooldown -= 1

            self.wave_history.append(x)

            if len(self.wave_history) > self.wave_history_size:

                self.wave_history.pop(0)

            return False

        self.wave_history.append(x)

        if len(self.wave_history) > self.wave_history_size:

            self.wave_history.pop(0)

        if len(self.wave_history) < 4:

            return False

        previous_x = self.wave_history[-2]

        current_x = self.wave_history[-1]

        movement = current_x - previous_x

        if abs(movement) < 0.015:

            return False

        if movement > 0:

            current_direction = "RIGHT"

        else:

            current_direction = "LEFT"

        if self.wave_direction is None:

            self.wave_direction = current_direction

            return False

        if current_direction != self.wave_direction:

            self.wave_count += 1

            self.wave_direction = current_direction

        if self.wave_count >= self.wave_direction_changes_required:

            self.wave_count = 0

            self.wave_direction = None

            self.wave_cooldown = 20

            self.wave_active = True

            return True

        return False

    def reset_wave(self):

        self.wave_history.clear()

        self.wave_direction = None

        self.wave_count = 0

        self.wave_active = False

        self.wave_cooldown = 0

    # ------------------------------------------------------------
    # GRAB
    # ------------------------------------------------------------

    def grab(self, obj, axes):

        if self.is_grabbing:

            return

        self.selected_object = obj

        self.is_grabbing = True

        self.grab_axes = axes

        self.grab_rotation = obj.rotation.copy()

        self.grab_scale = obj.scale.copy()

    # ------------------------------------------------------------
    # RELEASE
    # ------------------------------------------------------------

    def release(self):

        self.is_grabbing = False

        self.selected_object = None

        self.grab_axes = None

        self.grab_rotation = None

        self.grab_scale = None