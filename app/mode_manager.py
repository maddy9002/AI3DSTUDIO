class ModeManager:

    OBJECT = "OBJECT"
    EDIT = "EDIT"

    def __init__(self):

        self.current_mode = self.OBJECT

    # -----------------------------
    # Get Current Mode
    # -----------------------------

    def get_mode(self):

        return self.current_mode

    # -----------------------------
    # Set Mode
    # -----------------------------

    def set_mode(self, mode):

        if mode in (self.OBJECT, self.EDIT):

            self.current_mode = mode

    # -----------------------------
    # Toggle Mode
    # -----------------------------

    def toggle(self):

        if self.current_mode == self.OBJECT:

            self.current_mode = self.EDIT

        else:

            self.current_mode = self.OBJECT

    # -----------------------------
    # Helpers
    # -----------------------------

    def is_object_mode(self):

        return self.current_mode == self.OBJECT

    def is_edit_mode(self):

        return self.current_mode == self.EDIT