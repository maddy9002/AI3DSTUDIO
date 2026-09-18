import cv2
import mediapipe as mp
import math
import numpy as np

from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions


print("LOADED HAND TRACKER")


class HandTracker:

    def __init__(self):

        model_path = "models/hand_landmarker.task"

        self.grab_pinch_distance = None
        self.grab_scale = None

        base_options = BaseOptions(
            model_asset_path=model_path
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2
        )

        self.detector = vision.HandLandmarker.create_from_options(
            options
        )

        self.last_result = None

    def get_hand_position(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(
            mp_image
        )

        self.last_result = result

        if result.hand_landmarks:

            hand = result.hand_landmarks[0]

            index_tip = hand[8]

            return (
                index_tip.x,
                index_tip.y
            )

        return None

    def is_pinching(self):

        if self.last_result is None:
            return False

        if not self.last_result.hand_landmarks:
            return False

        hand = self.last_result.hand_landmarks[0]

        thumb_tip = hand[4]
        index_tip = hand[8]

        dx = thumb_tip.x - index_tip.x
        dy = thumb_tip.y - index_tip.y

        distance = (
            dx * dx +
            dy * dy
        ) ** 0.5

        return distance < 0.05

    def get_palm_position(self):

        if self.last_result is None:
            return None

        if not self.last_result.hand_landmarks:
            return None

        hand = self.last_result.hand_landmarks[0]

        wrist = hand[0]
        index = hand[5]
        pinky = hand[17]

        x = (
            wrist.x +
            index.x +
            pinky.x
        ) / 3

        y = (
            wrist.y +
            index.y +
            pinky.y
        ) / 3

        z = (
            wrist.z +
            index.z +
            pinky.z
        ) / 3

        return (
            x,
            y,
            z
        )

    def get_palm_axes(self):

        if self.last_result is None:
            return None

        if not self.last_result.hand_landmarks:
            return None

        hand = self.last_result.hand_landmarks[0]

        wrist = np.array([
            hand[0].x,
            hand[0].y,
            hand[0].z
        ])

        index = np.array([
            hand[5].x,
            hand[5].y,
            hand[5].z
        ])

        pinky = np.array([
            hand[17].x,
            hand[17].y,
            hand[17].z
        ])

        center = (index + pinky) / 2

        right = index - pinky
        up = center - wrist

        right_length = np.linalg.norm(right)

        if right_length == 0:
            return None

        right = right / right_length

        up_length = np.linalg.norm(up)

        if up_length == 0:
            return None

        up = up / up_length

        forward = np.cross(
            right,
            up
        )

        forward_length = np.linalg.norm(forward)

        if forward_length == 0:
            return None

        forward = forward / forward_length

        up = np.cross(
            forward,
            right
        )

        up_length = np.linalg.norm(up)

        if up_length == 0:
            return None

        up = up / up_length

        return (
            right,
            up,
            forward
        )

    def get_palm_matrix(self):

        axes = self.get_palm_axes()

        if axes is None:
            return None

        return np.column_stack(axes)

    def get_pinch_distance(self):

        if self.last_result is None:
            return None

        if not self.last_result.hand_landmarks:
            return None

        hand = self.last_result.hand_landmarks[0]

        thumb = hand[4]
        index = hand[8]

        dx = thumb.x - index.x
        dy = thumb.y - index.y
        dz = thumb.z - index.z

        return math.sqrt(
            dx * dx +
            dy * dy +
            dz * dz
        )

    def get_two_hand_palm_positions(self):

        if self.last_result is None:
            return []

        if not self.last_result.hand_landmarks:
            return []

        positions = []

        for hand in self.last_result.hand_landmarks:

            wrist = hand[0]
            index = hand[5]
            pinky = hand[17]

            x = (
                wrist.x +
                index.x +
                pinky.x
            ) / 3

            y = (
                wrist.y +
                index.y +
                pinky.y
            ) / 3

            z = (
                wrist.z +
                index.z +
                pinky.z
            ) / 3

            positions.append(
                (x, y, z)
            )

        return positions

    def get_two_hand_distance(self):

        positions = self.get_two_hand_palm_positions()

        if len(positions) != 2:
            return None

        hand_a = positions[0]
        hand_b = positions[1]

        dx = hand_a[0] - hand_b[0]
        dy = hand_a[1] - hand_b[1]
        dz = hand_a[2] - hand_b[2]

        return math.sqrt(
            dx * dx +
            dy * dy +
            dz * dz
        )

    def are_two_hands_pinching(self):

        if self.last_result is None:
            return False

        if not self.last_result.hand_landmarks:
            return False

        if len(self.last_result.hand_landmarks) != 2:
            return False

        for hand in self.last_result.hand_landmarks:

            thumb = hand[4]
            index = hand[8]

            dx = thumb.x - index.x
            dy = thumb.y - index.y
            dz = thumb.z - index.z

            distance = math.sqrt(
                dx * dx +
                dy * dy +
                dz * dz
            )

            if distance >= 0.07:
                return False

        return True

    def _is_finger_extended(
        self,
        hand,
        tip_index,
        pip_index
    ):

        tip = hand[tip_index]
        pip = hand[pip_index]
        wrist = hand[0]

        tip_distance = math.sqrt(
            (tip.x - wrist.x) ** 2 +
            (tip.y - wrist.y) ** 2 +
            (tip.z - wrist.z) ** 2
        )

        pip_distance = math.sqrt(
            (pip.x - wrist.x) ** 2 +
            (pip.y - wrist.y) ** 2 +
            (pip.z - wrist.z) ** 2
        )

        return tip_distance > pip_distance * 1.10

    def get_extended_finger_count(self):

        if self.last_result is None:
            return 0

        if not self.last_result.hand_landmarks:
            return 0

        if len(self.last_result.hand_landmarks) != 1:
            return 0

        hand = self.last_result.hand_landmarks[0]

        index_extended = self._is_finger_extended(
            hand,
            8,
            6
        )

        middle_extended = self._is_finger_extended(
            hand,
            12,
            10
        )

        ring_extended = self._is_finger_extended(
            hand,
            16,
            14
        )

        pinky_extended = self._is_finger_extended(
            hand,
            20,
            18
        )

        count = 0

        if index_extended:
            count += 1

        if middle_extended:
            count += 1

        if ring_extended:
            count += 1

        if pinky_extended:
            count += 1

        return count

    def get_gesture(self):

        if self.last_result is None:
            return "UNKNOWN"

        if not self.last_result.hand_landmarks:
            return "UNKNOWN"

        if len(self.last_result.hand_landmarks) == 2:

            if self.are_two_hands_pinching():
                return "TWO_HAND_PINCH"

            return "TWO_HANDS"

        hand = self.last_result.hand_landmarks[0]

        if self.is_pinching():
            return "PINCH"

        finger_count = self.get_extended_finger_count()

        if finger_count == 1:
            return "ONE_FINGER"

        if finger_count == 2:
            return "TWO_FINGERS"

        if finger_count == 3:
            return "THREE_FINGERS"

        if finger_count == 4:
            return "OPEN_HAND"

        return "FIST"