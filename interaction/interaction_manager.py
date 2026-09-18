class InteractionManager:

    def __init__(self):

        self.selected_object = None

        self.is_holding = False

        self.previous_pinch = False

        self.grab_offset = [0, 0, 0]

    def update_grab(self, pinching):

        # Detect only the transition from
        # not pinching -> pinching.

        grab_started = (
            pinching
            and not self.previous_pinch
        )

        grab_ended = (
            not pinching
            and self.previous_pinch
        )

        # Always update the previous state
        # before returning.

        self.previous_pinch = pinching

        if grab_started:

            self.is_holding = True

            print(
                "Holding:",
                self.is_holding
            )

            return True

        if grab_ended:

            self.is_holding = False

            print(
                "Holding:",
                self.is_holding
            )

            return True

        return False