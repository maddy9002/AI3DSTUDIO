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
            num_hands=1
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

        # Wrist
        wrist = hand[0]

        # Index MCP
        index = hand[5]

        # Pinky MCP
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

        # Normalize

        right = right / np.linalg.norm(right)

        up = up / np.linalg.norm(up)

        forward = np.cross(right, up)

        forward = forward / np.linalg.norm(forward)

        # Recalculate Up so all three vectors stay perfectly perpendicular

        up = np.cross(forward, right)

        up = up / np.linalg.norm(up)

        return (

            right,

            up,

            forward

        )
    
    def get_palm_matrix(self):

        axes = self.get_palm_axes()

        if axes is None:
            return None

        import numpy as np

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
            dx*dx +
            dy*dy +
            dz*dz
        )