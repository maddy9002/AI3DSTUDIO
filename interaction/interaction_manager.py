class InteractionManager:

    def __init__(self):

        self.selected_object = None

        self.is_holding = False

        self.previous_pinch = False

        self.grab_offset = [0, 0, 0]

    def update_grab(self, pinching):

        # Detect only a new pinch
        if pinching and not self.previous_pinch:

            self.is_holding = not self.is_holding

            print("Holding:", self.is_holding)

            return True

        self.previous_pinch = pinching

        return False